import importlib
import ipaddress
import os
import pickle
import sqlite3
from datetime import datetime
from hashlib import md5
from random import choice
from secrets import token_hex
from typing import Optional, Dict, Union, List, Literal

from .fs import Directory, File, StandardFS, FSBaseObject
from .helpers import SysCallStatus, SysCallMessages
from .services.service import Service
from .session import Session
from .user import User, Group


class Computer:
    def __init__(self) -> None:
        """
        The class object representing a basic linux computer. This class is the base for all nodes on a network
        """
        self.connection = sqlite3.connect("blackhat.db")
        self.database = self.connection.cursor()
        self.boot_time = datetime.now()
        self.parent: Optional[Computer, Router, ISPRouter] = None  # Router
        self.hostname: Optional[str] = None
        self.users: Dict[int, User] = {}
        self.groups: Dict[int, Group] = {}
        self.sessions: List[Session] = []
        self.lan = None
        self.id = token_hex(8)
        self.shell = None
        # Root user needs to be created before the FS is initialized (FS needs root to have a password to create /etc/passwd)
        self.init()

        # self.create_root_user()

        self.fs: StandardFS = StandardFS(self)
        self.services: dict[int, Service] = {}
        self.post_fs_init()

    def init(self) -> None:
        """
        Functions ran when a computer is booted (pre file-system setup/pre root user creation)

        Returns:
            None
        """
        self.boot_time = datetime.now()
        # Try to setup the user, group, and group membership tables
        init_tables = open("blackhat/database/init_tables.sql").read()
        self.database.executescript(init_tables)

        # Check if the computer we're initializing already exists in the database (we're loading an existing save)
        result = self.database.execute("SELECT * FROM computer WHERE id=?", (self.id,)).fetchall()

        if len(result) == 0:
            # We're starting a new save, lets save a copy of this computers id in the database, along with create the root user
            self.database.execute("INSERT INTO computer VALUES (?)", (self.id,))
            self.create_root_user()
            self.connection.commit()

    def post_fs_init(self) -> None:
        """
        Function ran after the file system and root user were initialized

        Returns:
            None
        """
        self.update_hostname()
        self.update_user_and_group_files()
        self.update_user_and_group_files()

    def run_command(self, command: str, args: Union[str, List[str], None], pipe: bool) -> SysCallStatus:
        """
        Runs a system binary or an external binary

        Args:
            command (str): The command or binary to run
            args (list): A list of arguments passed to the command or binary
            pipe (bool): If a pipe was used (used for routing input/output)

        Returns:
            SysCallStatus: A `SysCallStatus` object that contains a success status and some response data (changed on a case-by-case basis)
        """
        # The way that the path works is that if there are 2 binaries with the same name in 2 different directories,
        # The one that matches first in the path gets run
        # For example, if ls is in /etc/ and in /bin/ and the path is PATH=/home:/bin:/etc, the one in bin will run
        # For example, if ls is in /etc/ and in /bin/ and the path is PATH=/home:/etc:/bin, the one in etc will run
        try:
            bin_dirs_text = self.sessions[-1].env.get("PATH").split(":")
            bin_dirs = []

            for dir in bin_dirs_text:
                find_dir = self.fs.find(dir)
                if find_dir.success:
                    bin_dirs.append(find_dir.data)
        except AttributeError:
            find_bin = self.fs.find("/bin")
            if find_bin.success:
                bin_dirs = [find_bin.data]
            else:
                bin_dirs = []

        if len(bin_dirs) == 0:
            print(f"{command}: command not found")
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        exists = False

        for dir in bin_dirs:
            if command in list(dir.files.keys()):
                to_run = True
                break
        else:
            print(f"{command}: command not found")
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        try:
            module = importlib.import_module(f"blackhat.bin.{command}")
            response = module.main(self, args, pipe)
            if os.getenv("DEBUGMODE") == "false":
                self.save()

            return response
        except ImportError as e:
            try:
                module = importlib.import_module(f"blackhat.bin.installable.{command}")
                response = module.main(self, args, pipe)
                if os.getenv("DEBUGMODE") == "false":
                    self.save()

                return response
            except ImportError as e:
                print(f"There was an error when running command: {command}")
                return SysCallStatus(success=False, message=SysCallMessages.GENERIC)

    def set_hostname(self, hostname: str) -> SysCallStatus:
        """
        An easy function to update the hostname (also updates /etc/hostname)
        Args:
            hostname (str): The `Computer`'s new hostname

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately.
        """
        # Try to find the hostname file
        find_etc_hostname = self.fs.find("/etc/hostname")

        if not find_etc_hostname.success:
            # Make sure we at least have the /etc/ dir
            find_etc = self.fs.find("/etc")
            if not find_etc.success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
            else:
                # Create the /etc/hostname
                hostname_file = File("hostname", hostname, find_etc.data, 0, 0)
                find_etc.data.add_file(hostname_file)
        else:
            find_etc_hostname.data.content = hostname

        self.hostname = hostname
        return SysCallStatus(success=True)

    def update_hostname(self) -> None:
        """
        Reads /etc/hostname and sets the system hostname accordingly
        If /etc/hostname doesn't exist, the hostname is set to "localhost"

        Returns:
            None
        """
        etc_dir: Directory = self.fs.files.find("etc")

        if not etc_dir:
            self.hostname = "localhost"

        else:
            hostname_file: File = etc_dir.find("hostname")

            if not hostname_file:
                self.hostname = "localhost"
            else:
                self.hostname = hostname_file.content.split("\n")[0]

    def add_user(self, username: str, password: str, uid: Optional[int] = None, plaintext=True) -> SysCallStatus:
        """
        Add a new user to the system.
        This function also generates the UID for the new user (unless manually specified)

        Args:
            username (str): The username for the new user
            password (str): The plaintext password for the new user
            uid (int, optional): The UID of the new user
                        plaintext (bool): If the given `new_password` is plain text or an MD5 hash

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately. The `data` flag contains the new users UID if successful.
        """
        if self.find_user(username=username).success:
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

        # new_user = User(username)
        # new_user.set_password(password)

        # Manually specific UID
        if uid:
            # Check if a user with the given UID already exists
            if self.find_user(uid=uid).success:
                return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)
            else:
                next_uid = uid
        # Auto-generate the UID (depending on the situation)
        else:
            # We're creating our root user, there isn't going to be a previous UID
            users = self.get_all_users().data
            if len(users) == 0:
                next_uid = 0
            else:
                # Get the UID from the previously created user
                last_uid = users[-1].uid
                if last_uid == 0:
                    next_uid = 1000
                else:
                    next_uid = last_uid + 1

        # Hash the password before saving to the database
        hashed_password = md5(password.encode()).hexdigest() if plaintext else password

        # Create the new user
        self.database.execute("INSERT INTO blackhat_user (uid, username, password, computer_id) VALUES (?, ?, ?, ?)",
                              (next_uid, username, hashed_password, self.id))
        self.connection.commit()

        return SysCallStatus(success=True, data=next_uid)

    def delete_user(self, username: str) -> SysCallStatus:
        """
        Deletes a user from the system (by username)

        Args:
            username (str): The username of the user to delete

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately.
        """
        if self.find_user(username=username).success:
            self.database.execute("DELETE FROM blackhat_user WHERE computer_id=? and username=?", (self.id, username))
            self.connection.commit()
            return SysCallStatus(success=True)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def change_user_password(self, uid: int, new_password: str, plaintext=True) -> SysCallStatus:
        """
        Change the password of the user by uid

        Args:
            uid (int): The UID of the `User` to change the password of
            new_password (str): The MD5 hash of the password
            plaintext (bool): If the given `new_password` is plain text or an MD5 hash

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set accordingly.
        """
        # Double check that the user with the given UID exists
        lookup_user = self.find_user(uid=uid)
        if not lookup_user.success:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        # Hash the plain text password
        password_hash = md5(new_password.encode()).hexdigest() if plaintext else new_password

        # Update the password in the database
        result = self.database.execute("UPDATE blackhat_user SET password=? WHERE uid=? AND computer_id=?",
                                       (password_hash, uid, self.id))
        self.connection.commit()
        return SysCallStatus(success=True)

    def change_user_uid(self, uid: int, new_uid: int) -> SysCallStatus:
        """
        Change the uid of the user by uid

        Args:
            uid (int): The UID of the `User` to change the uid of
            new_uid (int): The new uid of the given user

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set accordingly.
        """
        # Double check that the user with the given UID exists
        lookup_user = self.find_user(uid=uid)
        if not lookup_user.success:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        # Make sure that no other user has the given `new_uid`
        lookup_user = self.find_user(uid=new_uid)
        if lookup_user.success:
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

        # Update the uid in the database
        result = self.database.execute("UPDATE blackhat_user SET uid=? WHERE uid=? AND computer_id=?",
                                       (new_uid, uid, self.id))
        self.connection.commit()

        # We need to update the UID of all sessions that this user has
        for session in self.sessions:
            if session.real_uid == uid:
                session.real_uid = new_uid

            if session.effective_uid == uid:
                session.effective_uid = new_uid

        # We also need to update the UID in the group membership records
        self.database.execute("UPDATE group_membership SET user_uid=? WHERE user_uid=? AND computer_id=?",
                              (new_uid, uid, self.id))

        return SysCallStatus(success=True)

    def add_group(self, name: str, gid: Optional[int] = None) -> SysCallStatus:
        """
        Add a new group to the system.
        This function also generates the GID for the new group (unless manually specified)

        Args:
            name (str): The name for the new group
            gid (int, optional): The GID of the new user

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately. The `data` flag contains the GID if successful.
        """
        if self.find_group(name=name).success:
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

        if gid:
            # Check if a group with the given GID already exists
            if self.find_group(gid=gid, name=name).success:
                return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)
            else:
                next_gid = gid
        else:
            # Auto-generate the GID (depending on the situation)
            groups = self.get_all_groups().data
            if len(groups) == 0:
                next_gid = 0
            else:
                # Get the GID from the previously created group
                last_gid = groups[-1].gid
                if last_gid == 0:
                    next_gid = 1000
                else:
                    next_gid = last_gid + 1

        # Create the new group and commit
        self.database.execute("INSERT INTO blackhat_group (gid, name, computer_id) VALUES (?, ?, ?)",
                              (next_gid, name, self.id))
        self.connection.commit()

        return SysCallStatus(success=True, data=next_gid)

    def delete_group(self, name: str) -> SysCallStatus:
        """
        Deletes a group from the system (by name)

        Args:
            name (str): The name of the group to delete

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately.
        """
        if self.find_group(name=name).success:
            self.database.execute("DELETE FROM blackhat_group WHERE computer_id=? and name=?", (self.id, name))
            self.connection.commit()
            return SysCallStatus(success=True)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def add_user_to_group(self, uid: int, gid: int,
                          membership_type: Literal["primary", "secondary"] = "secondary") -> SysCallStatus:
        """
        Add a user to a group (by uid and gid)

        Args:
            uid (int): The UID of the user
            gid (int): The GID of the group to add the user to
            membership_type (str): The type of group relationship (primary, secondary)

        Returns:
            SysCallStatus: A `SysCallStatus` object with the `success` flag set accordingly
        """
        # Confirm that both user and group exists
        if self.find_user(uid=uid).success and self.find_group(gid=gid).success:
            self.database.execute(
                "INSERT INTO group_membership (computer_id, user_uid, group_gid, membership_type) VALUES (?, ?, ?, ?)",
                (self.id, uid, gid, membership_type))
            self.connection.commit()
            return SysCallStatus(success=True)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def find_user_groups(self, uid: int) -> SysCallStatus:
        """
        Get the list of `Group` GID's that the `User` belongs to (by UID)

        Args:
            uid (int): The UID of the user to lookup

        Returns:
            SysCallStatus: A `SysCallStatus` with the `data` flag containing a list of GIDs
        """
        # Double check if the user exists
        if not self.find_user(uid=uid).success:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        else:
            # Ask the database for the GIDs
            result = self.database.execute("SELECT group_gid FROM group_membership WHERE computer_id=? and user_uid=?;",
                                           (self.id, uid)).fetchall()
            return SysCallStatus(success=True, data=[x[0] for x in result])

    def find_user_primary_group(self, uid: int) -> SysCallStatus:
        """
        Get the `Group` GID's that is the `User`s primary `Group` (by UID)

        Args:
            uid (int): The UID of the user to lookup

        Returns:
            SysCallStatus: A `SysCallStatus` with the `data` flag containing a list of GIDs
        """
        # Double check if the user exists
        if not self.find_user(uid=uid).success:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        else:
            # Ask the database for the GIDs
            result = self.database.execute(
                "SELECT group_gid FROM group_membership WHERE computer_id=? and user_uid=? and membership_type=?;",
                (self.id, uid, "primary")).fetchone()
            return SysCallStatus(success=True, data=[x for x in result])

    def find_users_in_group(self, gid: int) -> SysCallStatus:
        """
        Get a list of user UIDs that are part of the given groups GID

        Args:
            gid (int): The GID of the group to search

        Returns:
            SysCallStatus: A `SysCallStatus` with the `data` flag containing a list of UIDs
        """
        # Double check if the group exists
        if not self.find_group(gid=gid).success:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        # Ask the database for the UIDs
        result = self.database.execute(
            "SELECT uid FROM blackhat_user WHERE computer_id=? AND uid in (SELECT user_uid FROM group_membership WHERE computer_id=? AND group_gid=?)",
            (self.id, self.id, gid)).fetchall()

        return SysCallStatus(success=True, data=[x for x in result])

    def remove_user_from_group(self, uid: int, gid: int) -> SysCallStatus:
        """
        Remove a user from a group (by uid and gid)

        Args:
            uid (int): The UID of the user
            gid (int): The GID of the group to remove the user from

        Returns:
            SysCallStatus: A `SysCallStatus` object with the `success` flag set accordingly
        """
        # Confirm that both user and group exists
        if self.find_user(uid=uid).success and self.find_group(gid=gid).success:
            self.database.execute("DELETE FROM group_membership WHERE computer_id=? AND user_uid=? AND group_gid=?",
                                  (self.id, uid, gid))
            self.connection.commit()
            return SysCallStatus(success=True)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def find_user(self, uid: Optional[int] = None, username: Optional[str] = None) -> SysCallStatus:
        """
        Find a user in the database by UID or username
        Args:
            uid (int, optional): The UID of the user to find
            username (str, optional): The username of the user to find

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set accordingly. The `data` flag contains the user dict if found
        """
        if uid is None and username is None:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        else:
            result = self.database.execute("SELECT * FROM blackhat_user WHERE (uid=? OR username=?) AND computer_id=?",
                                           (uid, username, self.id)).fetchone()
            if not result:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

            return SysCallStatus(success=True,
                                 data=User(uid=result[1], username=result[2], password=result[3], full_name=result[4],
                                           room_number=result[5],
                                           work_phone=result[6], home_phone=result[7], other=result[8]))

    def find_group(self, gid: Optional[int] = None, name: Optional[str] = None) -> SysCallStatus:
        """
        Find a group in the database by GID or name or both
        Args:
            gid (int, optional): The GID of the group to find
            name (str, optional): The name of the group to find

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set accordingly. The `data` flag contains the group dict if found
        """
        if gid is None and name is None:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        # We're looking by name AND gid
        elif gid is not None and name is not None:
            result = self.database.execute("SELECT * FROM blackhat_group WHERE (gid=? AND name=?) AND computer_id=?",
                                           (gid, name, self.id)).fetchone()
        else:
            result = self.database.execute("SELECT * FROM blackhat_group WHERE (gid=? OR name=?) AND computer_id=?",
                                           (gid, name, self.id)).fetchone()

        if not result:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        return SysCallStatus(success=True, data=Group(gid=result[1], name=result[2]))

    def get_all_users(self) -> SysCallStatus:
        """
        Get all users that exist in the given system in the given format:

        Returns:
            SysCallStatus: A `SysCallStatus` with the `data` flag containing the array of `User`s
        """
        all_users = self.database.execute("SELECT * FROM blackhat_user WHERE computer_id=?",
                                          (self.id,)).fetchall()

        clean_users = []

        for user in all_users:
            clean_users.append(
                User(uid=user[1], username=user[2], password=user[3], full_name=user[4], room_number=user[5],
                     work_phone=user[6], home_phone=user[7], other=user[8]))
        return SysCallStatus(success=True, data=clean_users)

    def get_all_groups(self) -> SysCallStatus:
        """
        Get all groups that exist in the given system in the given format:

        Returns:
            SysCallStatus: A `SysCallStatus` with the `data` flag containing the array of `Group`s
        """
        all_groups = self.database.execute("SELECT * FROM blackhat_group WHERE computer_id=?",
                                           (self.id,)).fetchall()

        clean_groups = []

        for group in all_groups:
            clean_groups.append(Group(gid=group[1], name=group[2]))
        return SysCallStatus(success=True, data=clean_groups)

    def create_root_user(self) -> None:
        """
        Since the root user is different from "standard" users, and it must exist in any given system, it is manually
        created when the `Computer` is first initialized.

        Returns:
            None
        """
        # Add the root user with a random password
        # self.add_user("root", ''.join([choice(ascii_uppercase + digits) for _ in range(16)]))
        self.add_user("root", "password", uid=0)
        # Create the root group
        self.add_group('root', 0)

        # Add root to the root group
        self.add_user_to_group(0, 0, membership_type="primary")

    def update_user_and_group_files(self) -> SysCallStatus:
        """
        Makes sure that:
        /etc/passwd matches our internal user map
        /etc/shadow matches our internal user map
        /etc/group matches our internal group map

        Returns:
            None
        """
        etc_dir: Directory = self.fs.files.find("etc")

        if not etc_dir:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        passwd_file: File = etc_dir.find("passwd")
        shadow_file: File = etc_dir.find("shadow")
        group_file: File = etc_dir.find("group")

        # TODO: Allow modification of home directory from here
        # passwd format: USERNAME:MD5_PASSWORD OR "x":UID:PRIMARY_GID
        # shadow format: USERNAME:MD5_PASSWORD
        # group format: GROUP_NAME:x:GID:GROUP_USERS

        passwd_content = ""
        shadow_content = ""
        group_content = ""

        for user in self.get_all_users().data:
            # Find the "primary" group
            primary_group = self.find_user_primary_group(user.uid)
            if primary_group.success:
                if len(primary_group.data) > 0:
                    primary_group = primary_group.data[0]
                else:
                    primary_group = "?"
            else:
                primary_group = "?"

            passwd_content += f"{user.username}:x:{user.uid}:{primary_group}\n"
            shadow_content += f"{user.username}:{user.password}\n"

        for group in self.get_all_groups().data:
            uids = self.find_users_in_group(group.gid).data
            usernames = ""
            for uid in uids:
                user_lookup = self.find_user(uid=uid[0])
                usernames += ("?" if not user_lookup.success else user_lookup.data.username) + ","

            usernames = usernames[:-1]

            group_content += f"{group.name}:x:{group.gid}:{usernames}\n"
            # print(group_content, end="")

        if not passwd_file:
            # Create the /etc/passwd
            etc_dir.add_file(File("passwd", passwd_content, etc_dir, 0, 0))
        else:
            passwd_file.content = passwd_content

        if not shadow_file:
            # Create the /etc/shadow file and change its perms (rw-------)
            shadow_file = File("shadow", shadow_content, etc_dir, 0, 0)
            shadow_file.permissions = {"read": ["owner"], "write": ["owner"], "execute": []}
            etc_dir.add_file(shadow_file)
        else:
            shadow_file.content = shadow_content

        if not group_file:
            # Create the /etc/group
            etc_dir.add_file(File("group", group_content, etc_dir, 0, 0))
        else:
            group_file.content = group_content

        return SysCallStatus(success=True)

    def get_uid(self) -> int:
        """
        Returns the UID of the `Computer`'s current user
        Returns:
            int: UID of the `Computers`'s current user (from most recent session)
        """
        return self.sessions[-1].effective_uid

    def get_gid(self) -> int:
        """
        Returns the (primary) GID of the `Computer`'s current user
        Returns:
            int: (primary) GID of the `Computers`'s current user (from most recent session)
        """
        current_uid = self.get_uid()
        result = self.database.execute(
            "SELECT group_gid FROM group_membership WHERE computer_id=? AND user_uid=? AND membership_type=?",
            (self.id, current_uid, "primary")).fetchone()

        if result:
            return result[0]
        else:
            # NOTE: possible exploit, but maybe we leave it here on purpose?
            # TODO: Write proof of concept exploit to exploit this exploit
            return 0

    def get_pwd(self) -> FSBaseObject:
        """
        Get current directory in the file system

        Returns:
            FSBaseObjectSB: The  user's current directory
        """
        if len(self.sessions) == 0:
            return self.fs.files
        else:
            return self.sessions[-1].current_dir

    def get_env(self, key) -> Optional[str]:
        """
        Get an environment variable from the current session

        Args:
            key (str): The env var to retrieve

        Returns:
            str, optional: The matching value of the given key if found, otherwise, None
        """
        if len(self.sessions) == 0:
            return None
        else:
            return self.sessions[-1].env.get(key)

    def run_current_user_shellrc(self):
        """
        Run the .shellrc file in the current user's home folder (/home/<USERNAME>/.shellrc)
        The ".shellrc" file is replicating the behavior of .bashrc/.bash_profile/.zshrc (since we're not replicating one specific piece of software)

        Returns:
            None
        """
        current_username = self.find_user(self.get_uid()).data.username

        # Don't check /home/username, check /root for .shellrc
        if self.get_uid() == 0:
            shellrc_loc = "/root/.shellrc"
        else:
            shellrc_loc = f"/home/{current_username}/.shellrc"

        shellrc_lookup = self.fs.find(shellrc_loc)

        if shellrc_lookup.success:
            shellrc_lines = shellrc_lookup.data.read(self)

            if shellrc_lines.success:
                for line in shellrc_lines.data.split("\n"):
                    if line != "":
                        line = line.split()
                        result = self.run_command(line[0], line[1:], pipe=False)

    def save(self, output_file: str = "blackhat.save") -> bool:
        """
        Serialize and dump the current `Computer` (and everything that's connected to it (`StandardFS`, `File`s, etc)) to a file
        Args:
            output_file (str, optional): The file to dump the contents to

        Returns:
            bool: `True` if the dump/save was successful, otherwise `False`
        """
        if os.getenv("DEBUGMODE") == "false":
            try:
                with open(output_file, "wb") as f:
                    pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
                return True
            except Exception as e:
                # TODO: Fix save bug (can't pickle `self.connection` and `self.database`)
                return False
        else:
            return True

    def handle_tcp_connection(self, host: str, port: int, args: dict) -> SysCallStatus:
        """
        Route network traffic to a `Service` on the local `Computer`

        Args:
            host (str): The IP of the `Computer`
            port (int): The port the given `Service` in running on
            args (dict): A map of arguments to pass to the given `Service`

        Returns:
            SysCallMessage: A response generate by the `Service` or an error if no such `Service` exists.
        """
        if port in self.services.keys():
            return self.services[port].main(args)

        return SysCallStatus(success=False, message=SysCallMessages.GENERIC_NETWORK)

    def send_tcp(self, host: str, port: int, args: dict) -> SysCallStatus:
        """
        Pass a network connection to the router to route (either within the LAN or to an external LAN)

        Args:
            host (str): The IP address of the host to send the given `args` to
            port (int): The port on the given `host` in which the `Service` runs on
            args (dict): The data to send to the given `host` (processed by the `Service` on the other end)

        Returns:
            SysCallMessage: A response generate by the `Service` or an error if no such `Service` exists.
        """
        return self.parent.handle_tcp_connection(host, port, args)


class Router(Computer):
    def __init__(self) -> None:
        """
        This special type of `Computer` is made for handling network traffic between computers in a LAN
        This class represents what a real router would be in real life
        """
        super().__init__()
        self.clients = {}  # Format of clients: sorted by subnet then ID [1][2] (subnet 1 - ID 2)
        self.ip_pool: dict[int, list[str]] = {}
        self.wan = None
        self.lan = "192.168.1.1"
        self.port_forwarding = {}

    def dhcp(self, subnet: int) -> SysCallStatus:
        """
        Distributes IP addresses to clients on the network

        Args:
            subnet (int): subnet id to assign the client to

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the IP to assign to a given client.
        """
        # Split the router's IP to get the first 16 bits
        ip_split = self.lan.split(".")
        network_prefix = f"{ip_split[0]}.{ip_split[1]}.{subnet}"

        # Check if the IP pool for that subnet was generated already
        try:
            len(self.ip_pool[subnet])
        # If `self.ip_pool[<subnet>]` returns a key error, it was never created before
        except KeyError:
            # Generate a list of ips that are <NETWORK_PREFIX>.<subnet>.1-256
            self.ip_pool[subnet] = [f"{network_prefix}.{x}" for x in range(1, 257)]

        # Check if we have IP's left
        if len(self.ip_pool[subnet]) == 0:
            return SysCallStatus(success=False, message=SysCallMessages.EMPTY)

        # Choose a random ip from the pool
        ip = choice(self.ip_pool[subnet])

        # Remove the IP from the pool since it's in use
        self.ip_pool[subnet].remove(ip)
        return SysCallStatus(success=True, data=ip)

    def find_local_client(self, ip: str) -> SysCallStatus:
        """
        Finds a client (`Computer` object) in the local network by IP address

        Args:
            ip (str): The "private" IP of the client `Computer` to find

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `Computer` object if found.
        """
        subnet = ip.split(".")[2]
        for client in self.clients[int(subnet)].values():
            if client.lan == ip:
                return SysCallStatus(success=True, data=client)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def find_client(self, ip: str, port: Optional[int] = None) -> SysCallStatus:
        """
        A more "general" version of the `find_local_client()` function. This function determines if the given router will
        ask the `ISPRouter` for the given IP address or if the client is within the `Router`'s LAN

        Args:
            ip (str): The IP of the client `Computer` to find
            port (int, optional): The open port on the given client (find `Computer` behind another `Router` in an external LAN)

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `Computer` object if found.
        """
        # Check if the client belongs to ourselves (don't ask isp)
        ip_split = self.lan.split(".")
        network_prefix = f"{ip_split[0]}.{ip_split[1]}"

        # First check if we're looking for one of our own hosts
        if ip.startswith(network_prefix):
            # We're looking for ourselves
            if ip == self.lan:
                return SysCallStatus(success=True, data=self)
            else:
                client_ip_split = ip.split(".")
                subnet = client_ip_split[2]
                subnet_result = self.clients.get(int(subnet))
                if subnet_result:
                    client_result = next((x for x in subnet_result.values() if x.lan == ip), None)

                    if client_result:
                        return SysCallStatus(success=True, data=client_result)

                return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        else:

            # If the given ip is our wan address, another router is asking for a client
            if ip == self.wan:
                # If there is no port, we want the router (ourselves)
                if not port:
                    return SysCallStatus(success=True, data=self)
                else:
                    # We want a host at a specific open port
                    return self.find_client_by_port(port)
            # We're trying to find a client on another router, we do this by asking our router (the isp)
            else:
                # Ask the ISP for the router
                wan_client = self.parent.find_client(ip, port)
                if wan_client.success:
                    # We found the other router
                    # If there's no port, we're done (we wanted the router not a host behind the router)
                    if not port:
                        return SysCallStatus(success=True, data=wan_client.data)
                    else:
                        # If there is a port, we want to ask the external router for the client behind that port
                        # We can ask that router directly
                        return wan_client.data.find_client_by_port(port)
                else:
                    # Even the ISP couldn't find that router, it must not exist
                    return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def find_client_by_port(self, port: int) -> SysCallStatus:
        """
        Find a client in the given `Router`'s LAN by open port.
        Primarily used for finding the `Computer` hosting a given `Service` through an open port in the given `Router`

        Args:
            port (int): The port number (1-65535) of the given `Computer`

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `Computer` object if found.
        """
        ip_to_find = self.port_forwarding.get(port, None)
        if not ip_to_find:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        else:
            return SysCallStatus(success=True, data=ip_to_find)

    def add_new_client(self, client: Computer, subnet: int = 1) -> SysCallStatus:
        """
        Connect a given `Computer` to the given `Router`'s LAN.
        Also, assign an IP address using the `dhcp()` function.

        Args:
            client (Computer): The `Computer` instance to connect to the `Router`'s LAN
            subnet (int, optional): The subnet id to assign the given `Computer` to

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `client`'s newly assigned IP address if successful.
        """
        # Generate an IP for the client
        generate_ip_status = self.dhcp(subnet)
        # We we're unable to generate an IP for the given client
        if not generate_ip_status:
            return generate_ip_status

        # Assign the IP
        client.lan = generate_ip_status.data

        # Append to client to our client list
        try:
            last_id = list(self.clients[subnet].keys())[-1]
        except KeyError:
            last_id = 0

        # Check if the client subnet exists
        try:
            len(self.clients[subnet])
        except KeyError:
            # Init the subnet (empty)
            self.clients[subnet] = {}

        self.clients[subnet][last_id + 1] = client

        client.parent = self

        return SysCallStatus(success=True, data=client.lan)

    def resolve_dns(self, domain_name: str) -> SysCallStatus:
        """
        Ask the ISP to resolve a dns domain name to an IP address

        Args:
            domain_name (str): The domain name to resolve

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the IP of the given `domain_name` if found.
        """
        # Ask our parent (ISP router) to resolve a dns record
        return self.parent.resolve_dns(domain_name)

    def handle_tcp_connection(self, host: str, port: int, args: dict) -> SysCallStatus:
        """
        Handle network traffic routing within the `Router`'s LAN and between LANs

        Args:
            host (str): The IP address of the host to send the given `args` to
            port (int): The port on the given `host` in which the `Service` runs on
            args (dict): The data to send to the given `host` (processed by the `Service` on the other end)

        Returns:
            SysCallStatus: A `SysCallStatus` instance containing results about the connection (successful or not) and a response from the `Service` (if successful)
        """
        # If we don't manually check for our own ip, we end up in an infinite loop of trying to handle tcp connections
        if host == self.lan:
            if port in self.services.keys():
                return self.services[port].main(args)
            else:
                return SysCallStatus(success=False, message=SysCallMessages.GENERIC_NETWORK)
        client = self.find_client(host, port)
        if not client.success:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        else:
            return client.data.handle_tcp_connection(host, port, args)


class ISPRouter(Router):
    def __init__(self):
        """
        An ISP router is just a router of routers
        """
        super().__init__()
        # We're 1.1.1.1
        self.used_ips = ["1.1.1.1"]
        self.dns_records = {}

    def dhcp(self, **kwargs) -> SysCallStatus:
        """
        Distributes IP addresses to clients on the network

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the IP to assign to a given client.
        """
        while True:
            ip = ".".join(str(choice([x for x in range(1, 256) if x not in [192, 168]])) for _ in range(4))
            if ip not in self.used_ips:
                self.used_ips.append(ip)
                return SysCallStatus(success=True, data=ip)

    def find_client(self, ip: str, port: Optional[int] = None) -> SysCallStatus:
        """
        Finds a client `Computer` in connected to the given `ISPRouter`

        Args:
            ip (str): The IP of the client `Computer` to find
            port (int, optional): The open port on the given client (find `Computer` behind another `Router` in an external LAN)

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `Computer` object if found.
        """
        # Check if the computer we're looking for is ourselves (isp)
        if ip == self.lan:
            return SysCallStatus(success=True, data=self)

        # Check if the client is an IP or a domain
        try:
            is_ipv4 = ipaddress.ip_address(ip)
        except ValueError:
            is_ipv4 = False

        if not is_ipv4:
            # Try to resolve the given dns record
            dns_result = self.resolve_dns(ip)

            if not dns_result.success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
            else:
                ip = dns_result.data

        find_client = next((x for x in self.clients.values() if x.wan == ip), None)
        if find_client:
            return SysCallStatus(success=True, data=find_client)

        # Client not found
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def add_new_client(self, client: Router, **kwargs) -> SysCallStatus:
        """
        Connect a given `Computer` to the given `ISPRouter`
        Also, assign an IP address using the `dhcp()` function.

        Args:
            client (Computer): The `Computer` instance to connect to the `ISPRouter`

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `client`'s newly assigned IP address if successful.
        """
        dhcp_result = self.dhcp()
        if dhcp_result.success:
            client.wan = dhcp_result.data
            client.parent = self
            self.clients[client.wan] = client
            return SysCallStatus(success=True, data=client.wan)
        else:
            # Failed for some reason (DHCP will give us our error)
            return dhcp_result

    def add_dns_record(self, domain_name: str, ip: str) -> SysCallStatus:
        """
        Add a new record to the given `ISPRouters` DNS records table

        Args:
            domain_name (str): The domain name of the record
            ip (str): The IP address that the given `domain_name` should resolve to

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately.
        """
        if domain_name in self.dns_records.keys():
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

        self.dns_records[domain_name] = ip
        return SysCallStatus(success=True)

    def remove_dns_record(self, domain_name):
        """
        Remove an existing record from the given `ISPRouters` DNS records table

        Args:
            domain_name (str): The domain name of the record to be removed

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately.
        """
        if domain_name in self.dns_records.keys():
            del self.dns_records[domain_name]
            return SysCallStatus(success=True)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def resolve_dns(self, domain_name: str) -> SysCallStatus:
        """
        Find the IP address linked to the given `domain_name`

        Args:
            domain_name (str): The domain name to resolve

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the resolved IP address if found.
        """
        dns_record = self.dns_records.get(domain_name, None)
        if dns_record:
            return SysCallStatus(success=True, data=dns_record)

        # Failed to find
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
