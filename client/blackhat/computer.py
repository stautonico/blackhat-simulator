import importlib
import os
import pickle
import sqlite3
from datetime import datetime
from hashlib import md5
from os import system as real_syscall
from platform import system
from random import choice
from secrets import token_hex
from time import time, sleep
from typing import Optional, Dict, Union, List, Literal

from .fs import Directory, File, StandardFS, FSBaseObject, copy
from .helpers import Result, ResultMessages, AccessMode, timeval, stat_struct, RebootMode
from .lib import unistd, stdlib, dirent, fcntl, stdio, pwd, ifaddrs, netdb
from .lib.arpa import inet
from .lib.sys import time, stat, socket
from .lib.sys.socket import Socket
from .services.pingserver import PingServer
from .services.service import Service
from .session import Session
from .user import User, Group

from importlib.machinery import SourceFileLoader


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
        self.services: dict[int, Service] = {0: PingServer(self)}
        self.post_fs_init()

    ##################
    # Init functions #
    ##################

    def init(self) -> None:
        """
        Functions ran when a computer is booted (pre file-system setup/pre root user creation)

        Returns:
            None
        """
        self.boot_time = datetime.now()
        # Try to setup the user, group, and group membership tables
        init_tables_file = open("blackhat/database/init_tables.sql")
        init_tables = init_tables_file.read()
        self.database.executescript(init_tables)

        # Check if the computer we're initializing already exists in the database (we're loading an existing save)
        result = self.database.execute("SELECT * FROM computer WHERE id=?", (self.id,)).fetchall()

        if len(result) == 0:
            # We're starting a new save, lets save a copy of this computers id in the database, along with create the root user
            self.database.execute("INSERT INTO computer VALUES (?)", (self.id,))
            self.create_root_user()
            self.connection.commit()

        init_tables_file.close()

    def post_fs_init(self) -> None:
        """
        Function ran after the file system and root user were initialized

        Returns:
            None
        """
        self.sync_hostname()
        self.sync_user_and_group_files()

    def update_libs(self):
        """
        The system libraries need access to the given `Computer` object, so before a command runs, we pass a reference
        to the current `Computer` object, so the binaries don't need `computer` in their arguments (prevents cheating in
        binaries). If commands had access to a `Computer` object, they could just read files without permission, access
        user passwords that they shouldn't, change current UID when they shouldn't, etc.

        Returns:
            None
        """
        libs = [unistd, time, stat, stdlib, dirent, fcntl, inet, stdio, pwd, socket, ifaddrs, netdb]

        for lib in libs:
            lib.update(self)

    ##############
    # Sync files #
    ##############

    def sync_hostname(self) -> None:
        """
        Reads /etc/hostname and sets the system hostname accordingly
        If /etc/hostname doesn't exist, the hostname is set to "localhost"

        Returns:
            None
        """
        # Note: We don't need to use the sethostname syscall because this is only if we updated the /etc/hostname file
        etc_dir: Directory = self.fs.files.find("etc")

        if not etc_dir:
            self.hostname = "localhost"

        else:
            hostname_file: File = etc_dir.find("hostname")

            if not hostname_file:
                self.hostname = "localhost"
            else:
                self.hostname = hostname_file.content.split("\n")[0]

    def sync_user_and_group_files(self) -> Result:
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
            return Result(success=False, message=ResultMessages.NOT_FOUND)

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
            primary_group = self.get_user_primary_group(user.uid)
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
            uids = self.get_users_in_group(group.gid).data
            usernames = ""
            for uid in uids:
                user_lookup = self.get_user(uid=uid[0])
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

        return Result(success=True)

    def run_command(self, command: str, args: Union[str, List[str], None], pipe: bool) -> Result:
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
        self.update_libs()
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
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        for dir in bin_dirs:
            if command in list(dir.files.keys()):
                binary_object = dir.files[command]
                break
        else:
            print(f"{command}: command not found")
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        # TODO: Check that the "binary_object" is not a directory and has executable permission
        if binary_object.is_directory():
            print(f"shell: {command}: is a directory")
            return Result(success=False, message=ResultMessages.IS_DIRECTORY)

        # NOTE: Disabled for debugging
        # if not binary_object.check_perm("execute", self).success:
        #     print(f"shell: permission denied: {command}")
        #     return Result(success=False, message=ResultMessages.NOT_ALLOWED_EXECUTE)


        random_filename = f"/tmp/{token_hex(6)}.py"

        with open(random_filename, "w") as f:
            f.write(binary_object.content)

        # If the binary is a setuid, we will change the uid
        if binary_object.setuid:
            self.sessions[-1].effective_uid = binary_object.owner
            # self.sys_setuid(binary_object.owner)

        try:
            module = SourceFileLoader("main",
                                      random_filename).load_module()

            response = module.main(args, pipe)

        except TypeError:
            # The code we're running doesn't take a pipe argument
            response = module.main(args)
        except Exception as e:
            if os.getenv("DEBUGMODE") == "true":
                print(f"segmentation fault (core dumped) ({e})  {command}")
            else:
                print(f"segmentation fault (core dumped)  {command}")

            return Result(success=False, message=ResultMessages.GENERIC)

        if not response:
            response = Result(success=False)
        else:
            if type(response) == int:
                response = Result(success=response==0)



        # Reset the UID (to prevent binaries from getting stuck with invalid uids)
        self.sessions[-1].effective_uid = self.sessions[-1].real_uid

        if os.getenv("DEBUGMODE") == "false":
            self.save()

        return response

    #################
    # User + Groups #
    #################

    def add_user(self, username: str, password: str, uid: Optional[int] = None, plaintext=True) -> Result:
        """
        Add a new user to the system.
        This function also generates the UID for the new user (unless manually specified)

        Args:
            username (str): The username for the new user
            password (str): The plaintext password for the new user
            uid (int, optional): The UID of the new user
                        plaintext (bool): If the given `new_password` is plain text or an MD5 hash

        Returns:
            Result: A `Result` instance with the `success` flag set accordingly. The `data` flag contains the new users UID if successful.
        """
        if self.get_user(username=username).success:
            return Result(success=False, message=ResultMessages.ALREADY_EXISTS)

        # new_user = User(username)
        # new_user.set_password(password)

        # Manually specific UID
        if uid:
            # Check if a user with the given UID already exists
            if self.get_user(uid=uid).success:
                return Result(success=False, message=ResultMessages.ALREADY_EXISTS)
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
                    user_with_next_uid = self.get_user(uid=next_uid)

                    while user_with_next_uid.success:
                        next_uid += 1
                        user_with_next_uid = self.get_user(uid=next_uid)

        # Hash the password before saving to the database
        hashed_password = md5(password.encode()).hexdigest() if plaintext else password

        # Create the new user
        self.database.execute("INSERT INTO blackhat_user (uid, username, password, computer_id) VALUES (?, ?, ?, ?)",
                              (next_uid, username, hashed_password, self.id))
        self.connection.commit()

        return Result(success=True, data=next_uid)

    def delete_user(self, username: str) -> Result:
        """
        Deletes a user from the system (by username)

        Args:
            username (str): The username of the user to delete

        Returns:
            Result: A `Result` instance with the `success` flag set accordingly.
        """
        if self.get_user(username=username).success:
            self.database.execute("DELETE FROM blackhat_user WHERE computer_id=? and username=?", (self.id, username))
            self.connection.commit()
            return Result(success=True)

        return Result(success=False, message=ResultMessages.NOT_FOUND)

    def change_user_password(self, uid: int, new_password: str, plaintext=True) -> Result:
        """
        Change the password of the user by uid

        Args:
            uid (int): The UID of the `User` to change the password of
            new_password (str): The MD5 hash of the password
            plaintext (bool): If the given `new_password` is plain text or an MD5 hash

        Returns:
            Result: A `Result` with the `success` flag set accordingly.
        """
        # Double check that the user with the given UID exists
        lookup_user = self.get_user(uid=uid)
        if not lookup_user.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        # Hash the plain text password
        password_hash = md5(new_password.encode()).hexdigest() if plaintext else new_password

        # Update the password in the database
        result = self.database.execute("UPDATE blackhat_user SET password=? WHERE uid=? AND computer_id=?",
                                       (password_hash, uid, self.id))
        self.connection.commit()
        return Result(success=True)

    def change_user_uid(self, uid: int, new_uid: int) -> Result:
        """
        Change the uid of the user by uid

        Args:
            uid (int): The UID of the `User` to change the uid of
            new_uid (int): The new uid of the given user

        Returns:
            Result: A `Result` with the `success` flag set accordingly.
        """
        # Double check that the user with the given UID exists
        lookup_user = self.get_user(uid=uid)
        if not lookup_user.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        # Make sure that no other user has the given `new_uid`
        lookup_user = self.get_user(uid=new_uid)
        if lookup_user.success:
            return Result(success=False, message=ResultMessages.ALREADY_EXISTS)

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

        return Result(success=True)

    def add_group(self, name: str, gid: Optional[int] = None) -> Result:
        """
        Add a new group to the system.
        This function also generates the GID for the new group (unless manually specified)

        Args:
            name (str): The name for the new group
            gid (int, optional): The GID of the new user

        Returns:
            Result: A `Result` instance with the `success` flag set accordingly. The `data` flag contains the GID if successful.
        """
        if self.get_group(name=name).success:
            return Result(success=False, message=ResultMessages.ALREADY_EXISTS)

        if gid:
            # Check if a group with the given GID already exists
            if self.get_group(gid=gid, name=name).success:
                return Result(success=False, message=ResultMessages.ALREADY_EXISTS)
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

        return Result(success=True, data=next_gid)

    def delete_group(self, name: str) -> Result:
        """
        Deletes a group from the system (by name)

        Args:
            name (str): The name of the group to delete

        Returns:
            Result: A `Result` instance with the `success` flag set accordingly.
        """
        if self.get_group(name=name).success:
            self.database.execute("DELETE FROM blackhat_group WHERE computer_id=? and name=?", (self.id, name))
            self.connection.commit()
            return Result(success=True)

        return Result(success=False, message=ResultMessages.NOT_FOUND)

    def add_user_to_group(self, uid: int, gid: int,
                          membership_type: Literal["primary", "secondary"] = "secondary") -> Result:
        """
        Add a user to a group (by uid and gid)

        Args:
            uid (int): The UID of the user
            gid (int): The GID of the group to add the user to
            membership_type (str): The type of group relationship (primary, secondary)

        Returns:
            Result: A `Result` object with the `success` flag set accordingly
        """
        # Confirm that both user and group exists
        if self.get_user(uid=uid).success and self.get_group(gid=gid).success:
            self.database.execute(
                "INSERT INTO group_membership (computer_id, user_uid, group_gid, membership_type) VALUES (?, ?, ?, ?)",
                (self.id, uid, gid, membership_type))
            self.connection.commit()
            return Result(success=True)
        else:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

    def get_user_groups(self, uid: int) -> Result:
        """
        Get the list of `Group` GID's that the `User` belongs to (by UID)

        Args:
            uid (int): The UID of the user to lookup

        Returns:
            Result: A `Result` with the `data` flag containing a list of GIDs
        """
        # Double check if the user exists
        if not self.get_user(uid=uid).success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)
        else:
            # Ask the database for the GIDs
            result = self.database.execute("SELECT group_gid FROM group_membership WHERE computer_id=? and user_uid=?;",
                                           (self.id, uid)).fetchall()
            return Result(success=True, data=[x[0] for x in result])

    def get_user_primary_group(self, uid: int) -> Result:
        """
        Get the `Group` GID's that is the `User`s primary `Group` (by UID)

        Args:
            uid (int): The UID of the user to lookup

        Returns:
            Result: A `Result` with the `data` flag containing a list of GIDs
        """
        # Double check if the user exists
        if not self.get_user(uid=uid).success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)
        else:
            # Ask the database for the GIDs
            result = self.database.execute(
                "SELECT group_gid FROM group_membership WHERE computer_id=? and user_uid=? and membership_type=?;",
                (self.id, uid, "primary")).fetchone()
            return Result(success=True, data=[x for x in result])

    def get_users_in_group(self, gid: int) -> Result:
        """
        Get a list of user UIDs that are part of the given groups GID

        Args:
            gid (int): The GID of the group to search

        Returns:
            Result: A `Result` with the `data` flag containing a list of UIDs
        """
        # Double check if the group exists
        if not self.get_group(gid=gid).success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)
        # Ask the database for the UIDs
        result = self.database.execute(
            "SELECT uid FROM blackhat_user WHERE computer_id=? AND uid in (SELECT user_uid FROM group_membership WHERE computer_id=? AND group_gid=?)",
            (self.id, self.id, gid)).fetchall()

        return Result(success=True, data=[x for x in result])

    def remove_user_from_group(self, uid: int, gid: int) -> Result:
        """
        Remove a user from a group (by uid and gid)

        Args:
            uid (int): The UID of the user
            gid (int): The GID of the group to remove the user from

        Returns:
            Result: A `Result` object with the `success` flag set accordingly
        """
        # Confirm that both user and group exists
        if self.get_user(uid=uid).success and self.get_group(gid=gid).success:
            self.database.execute("DELETE FROM group_membership WHERE computer_id=? AND user_uid=? AND group_gid=?",
                                  (self.id, uid, gid))
            self.connection.commit()
            return Result(success=True)
        else:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

    def get_user(self, uid: Optional[int] = None, username: Optional[str] = None) -> Result:
        """
        Find a user in the database by UID or username
        Args:
            uid (int, optional): The UID of the user to find
            username (str, optional): The username of the user to find

        Returns:
            Result: A `Result` with the `success` flag set accordingly. The `data` flag contains the user dict if found
        """
        if uid is None and username is None:
            return Result(success=False, message=ResultMessages.NOT_FOUND)
        else:
            result = self.database.execute("SELECT * FROM blackhat_user WHERE (uid=? OR username=?) AND computer_id=?",
                                           (uid, username, self.id)).fetchone()
            if not result:
                return Result(success=False, message=ResultMessages.NOT_FOUND)

            return Result(success=True,
                          data=User(uid=result[1], username=result[2], password=result[3], full_name=result[4],
                                    room_number=result[5],
                                    work_phone=result[6], home_phone=result[7], other=result[8]))

    def get_group(self, gid: Optional[int] = None, name: Optional[str] = None) -> Result:
        """
        Find a group in the database by GID or name or both
        Args:
            gid (int, optional): The GID of the group to find
            name (str, optional): The name of the group to find

        Returns:
            Result: A `Result` with the `success` flag set accordingly. The `data` flag contains the group dict if found
        """
        if gid is None and name is None:
            return Result(success=False, message=ResultMessages.NOT_FOUND)
        # We're looking by name AND gid
        elif gid is not None and name is not None:
            result = self.database.execute("SELECT * FROM blackhat_group WHERE (gid=? AND name=?) AND computer_id=?",
                                           (gid, name, self.id)).fetchone()
        else:
            result = self.database.execute("SELECT * FROM blackhat_group WHERE (gid=? OR name=?) AND computer_id=?",
                                           (gid, name, self.id)).fetchone()

        if not result:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        return Result(success=True, data=Group(gid=result[1], name=result[2]))

    def get_all_users(self) -> Result:
        """
        Get all users that exist in the given system in the given format:

        Returns:
            Result: A `Result` with the `data` flag containing the array of `User`s
        """
        all_users = self.database.execute("SELECT * FROM blackhat_user WHERE computer_id=?",
                                          (self.id,)).fetchall()

        clean_users = []

        for user in all_users:
            clean_users.append(
                User(uid=user[1], username=user[2], password=user[3], full_name=user[4], room_number=user[5],
                     work_phone=user[6], home_phone=user[7], other=user[8]))
        return Result(success=True, data=clean_users)

    def get_all_groups(self) -> Result:
        """
        Get all groups that exist in the given system in the given format:

        Returns:
            Result: A `Result` with the `data` flag containing the array of `Group`s
        """
        all_groups = self.database.execute("SELECT * FROM blackhat_group WHERE computer_id=?",
                                           (self.id,)).fetchall()

        clean_groups = []

        for group in all_groups:
            clean_groups.append(Group(gid=group[1], name=group[2]))
        return Result(success=True, data=clean_groups)

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

    def set_env(self, key: str, value: str) -> Result:
        """
        Set an environment variable to the current session

        Args:
            key (str): The env var to set
            value (str): The value of the new var to set

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        if len(self.sessions) == 0:
            return Result(success=False, message=ResultMessages.GENERIC)

        self.sessions[-1].env[key] = value
        return Result(success=True)

    def run_current_user_shellrc(self):
        """
        Run the .shellrc file in the current user's home folder (/home/<USERNAME>/.shellrc)
        The ".shellrc" file is replicating the behavior of .bashrc/.bash_profile/.zshrc (since we're not replicating one specific piece of software)

        Returns:
            None
        """
        current_username = self.get_user(self.sys_getuid()).data.username

        # Don't check /home/username, check /root for .shellrc
        if self.sys_getuid() == 0:
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
                        result = self.sys_execvp(line[0], line[1:])
                        # result = self.run_command(line[0], line[1:], pipe=False)

    def save(self, output_file: str = "blackhat.save") -> bool:
        """
        Serialize and dump the current `Computer` (and everything that's connected to it (`StandardFS`, `File`s, etc)) to a file
        Args:
            output_file (str, optional): The file to dump the contents to

        Returns:
            bool: `True` if the dump/save was successful, otherwise `False`
        """
        # Temporary: Disable saving because it doesn't work anyway
        if True == False:
            # if os.getenv("DEBUGMODE") == "false":
            try:
                with open(output_file, "wb") as f:
                    pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
                return True
            except Exception as e:
                # TODO: Fix save bug (can't pickle `self.connection` and `self.database`)
                return False
        else:
            return True

    ##############
    # Networking #
    ##############

    def resolve_dns(self, domain: str, dns_server: Optional[str] = None) -> Result:
        """
        Check all DNS servers in the /etc/resolv.conf unless a `dns_server` is specified

        args:
            domain (str): The domain name to lookup
            dns_server (str, optional) The DNS server to use to lookup the domain

        Returns:
            Result: A `Result` object with the success and data flag set accordingly
        """
        if dns_server:
            # We need to try to find the given dns server
            dns_servers = [dns_server]
        else:
            find_resolv_conf = self.fs.find("/etc/resolv.conf")
            dns_servers = []
            if find_resolv_conf.success:
                content = find_resolv_conf.data.content.split("\n")
                for line in content:
                    if line.startswith("nameserver "):
                        dns_servers.append(line[11:])

        for server in dns_servers:
            # Establish that the server exists
            server_obj = self.parent.find_client(server, 53)
            if server_obj.success:
                packet_result = server_obj.data.main({"domain": domain})

                if packet_result.success:
                    return Result(success=True, data=packet_result.data)

        return Result(success=False, message=ResultMessages.NOT_FOUND)

    ############
    # Syscalls #
    ############
    def sys_read(self, filepath: str) -> Result:
        """
        Try to read the content of the given `filepath`. Checks permissions

        Args:
            filepath (str): The path of the file to read

        Returns:
            Result: A `Result` object with the success flag set accordingly and the data flag containing the files
            if read was successful
        """
        # Try to find the file
        find_file = self.fs.find(filepath)

        if not find_file.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        if find_file.data.is_directory():
            return Result(success=False, message=ResultMessages.IS_DIRECTORY)

        try_read_file = find_file.data.read(self)

        if not try_read_file.success:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED_READ)

        return Result(success=True, data=try_read_file.data)

    def sys_write(self, fd: Union[str, Socket], data: Union[str, dict]) -> Result:
        """
        Try to write to a given file descriptor. If `fd` is a file path, this function will try to write to a file
        (permission safe), however, if the fd is a `Socket`, this function will try to send the given `data` to the
        respective `Socket`'s connected service (if connected).

        Args:
            fd (str or :obj:`Socket`): The filepath of the file or Socket to write to
            data (str or dict): The data to write to the file (if fd == str) or data to send to the socket (if fd == Socket)

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        if type(fd) == Socket:
            # We're 'writing' to a network socket
            if not fd.client:
                return Result(success=False, message=ResultMessages.NOT_CONNECTED)

            if type(data) == str:
                return Result(success=False, message=ResultMessages.INVALID_ARGUMENT)

            return fd.client.main(data)
        else:
            # We're writing to a file
            # Try to find the file
            find_file = self.fs.find(fd)

            if not find_file.success:
                return Result(success=False, message=ResultMessages.NOT_FOUND)

            if find_file.data.is_directory():
                return Result(success=False, message=ResultMessages.IS_DIRECTORY)

            try_write_file = find_file.data.write(data, self)

            if not try_write_file.success:
                return Result(success=False, message=ResultMessages.NOT_ALLOWED_WRITE)

            return Result(success=True)

    def sys_chown(self, pathname: str, owner: int, group: int) -> Result:
        """
        Change the owner of the given `pathname` (if allowed)

        Notes:
            Only the owner or root is allowed to change the owner of a `File`/`Directory`

        Args:
            pathname (str): The file path of the `File`/`Directory` to change the owner of
            owner (int): The UID of the new owner
            group (int): The GID of the new owner

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        find_file = self.fs.find(pathname)

        if not find_file.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        file = find_file.data

        change_perms = file.change_owner(self, owner, group)

        if not change_perms.success:
            return Result(success=False, message=change_perms.message)

        return Result(success=True)

    def sys_chdir(self, pathname: str) -> Result:
        """
        Change the `current_dir` of the current `Session`

        Args:
            pathname (str): The file path of the directory to `cd` into

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        find_file = self.fs.find(pathname)

        if not find_file.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        # We need executable permissions to cd (???)
        check_perm = find_file.data.check_perm("execute", self)
        if not check_perm.success:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

        if find_file.data.is_file():
            return Result(success=False, message=ResultMessages.IS_FILE)

        self.sessions[-1].current_dir = find_file.data
        return Result(success=True)

    def sys_getuid(self) -> int:
        """
        Returns the UID of the `Computer`'s current user

        Returns:
            int: UID of the `Computers`'s current user (from most recent session)
        """
        if len(self.sessions) == 0:
            return 0

        return self.sessions[-1].effective_uid

    def sys_setuid(self, uid: int) -> Result:
        """
        Change current `Session`'s effective UID to the given `UID`

        Notes:
            setuid() followed the current rules:
                * If the "caller" uid is root, change the uid to whatever is given
                * If the "caller" isn't root, BUT the setuid bit (not implement yet) is set, the UID can be set to the owner of the file
                * If the "caller" isn't root, and the setuid bit ISN'T set, deny all changes

        Args:
            uid (int): The new UID to change to

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        # TODO: Implement a PROPER setuid
        # The way setuid should work:
        # If the "caller" uid is root, change the uid to whatever is given
        # If the "caller" isn't root, BUT the setuid bit (not implement yet) is set, the UID can be set to the owner of the file
        # If the "caller" isn't root, and the setuid bit ISN'T set, deny all changes

        if self.sys_getuid() == 0:
            self.sessions[-1].effective_uid = uid

        return Result(success=True)
        # else:
        #     return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    def sys_getgid(self) -> int:
        """
        Returns the (primary) GID of the `Computer`'s current user

        Returns:
            int: (primary) GID of the `Computers`'s current user (from most recent session)
        """
        current_uid = self.sys_getuid()
        result = self.database.execute(
            "SELECT group_gid FROM group_membership WHERE computer_id=? AND user_uid=? AND membership_type=?",
            (self.id, current_uid, "primary")).fetchone()

        if result:
            return result[0]
        else:
            # NOTE: possible exploit, but maybe we leave it here on purpose?
            # TODO: Write proof of concept exploit to exploit this exploit
            return 0

    def sys_sethostname(self, hostname: str) -> Result:
        """
        An easy function to update the hostname (also updates /etc/hostname)
        Args:
            hostname (str): The `Computer`'s new hostname

        Returns:
            Result: A `Result` instance with the `success` flag set accordingly.
        """
        # Try to find the hostname file
        if self.sys_getuid() != 0:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

        if not self.sys_stat("/etc/hostname").success:
            # Make sure we at least have the /etc/ dir so we can make /etc/hostname
            if not self.sys_stat("/etc/").success:
                return Result(success=False, message=ResultMessages.NOT_FOUND)
            # Create the /etc/hostname
            find_etc_dir = self.fs.find("/etc/")
            find_etc_dir.data.add_file(File("hostname", hostname, find_etc_dir.data, 0, 0))
        else:
            # Even though we should never get here unless we're root, I'm gonna be a good boy and do this properly
            if not self.sys_write("/etc/hostname", hostname).success:
                return Result(success=False, message=ResultMessages.NOT_ALLOWED_WRITE)

        self.hostname = hostname
        return Result(success=True)

    def sys_gethostname(self) -> str:
        """
        Gets the current system hostname (from internal var, not /etc/hostname)

        Returns:
            str: "localhost" if the hostname isn't set, otherwise, the current `Computer`'s hostname
        """
        return "localhost" if not self.hostname else self.hostname

    def sys_getcwd(self) -> FSBaseObject:
        """
        Get current directory in the file system

        Returns:
            FSBaseObject: The  user's current directory
        """
        if len(self.sessions) == 0:
            return self.fs.files
        else:
            return self.sessions[-1].current_dir

    def sys_access(self, pathname: str, mode: int) -> Result:
        """
        Check if the current effective UID has a given permission to the given `File`/`Directory`
        Possible modes are:
            * F_OK: File exists
            * R_OK: Read permission
            * W_OK: Write permissions
            * X_OK: Execute permission

        Args:
            pathname (str): The file path of the given `File`/`Directory` to check
            mode (int): Bitwise flags of the permissions to check

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        # We need to find the file no matter what we do, so lets just find it now
        find_file = self.fs.find(pathname)

        success = True

        if not find_file.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        file = find_file.data

        if AccessMode.R_OK in mode:
            if not file.check_perm("read", self).success:
                success = False

        if AccessMode.W_OK in mode:
            if not file.check_perm("write", self).success:
                success = False

        if AccessMode.X_OK in mode:
            if not file.check_perm("execute", self).success:
                success = False

        return Result(success=success)

    def sys_gettimeofday(self) -> Result:
        """
        Get the current time (host systems time)

        Returns:
            timeval: A `timeval` struct containing the current time in seconds
        """
        # TODO: Add get time by timezone
        timestamp = time()
        seconds = int(timestamp)
        microseconds = int(str(timestamp - seconds).replace("0.", ""))

        return Result(success=True, data=timeval(seconds, microseconds))

    def sys_stat(self, path: str) -> Result:
        """
        Get information about a given file

        Args:
            path (str): The path of the given `File`/`Directory` to get info about

        Returns:
            Result: A `Result` object with the success flag set accordingly and the data flag containing a `stat_struct` object if successful
        """
        find_file = self.fs.find(path)

        if not find_file.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        # Do we need read permissions to stat this file?
        # if not find_file.data.check_perm("read", self).success:
        #    return Result(success=False, message=ResultMessages.NOT_ALLOWED)

        file = find_file.data

        is_file = file.is_file()

        # TODO: Find a less shit way to do this
        mode = [0, 0, 0]

        # Owner bit
        if "owner" in file.permissions["execute"]:
            mode[0] += 1
        if "owner" in file.permissions["write"]:
            mode[0] += 2
        if "owner" in file.permissions["read"]:
            mode[0] += 4
        # Group bit
        if "group" in file.permissions["execute"]:
            mode[1] += 1
        if "group" in file.permissions["write"]:
            mode[1] += 2
        if "group" in file.permissions["read"]:
            mode[1] += 4
        # Public bit
        if "public" in file.permissions["execute"]:
            mode[2] += 1
        if "public" in file.permissions["write"]:
            mode[2] += 2
        if "public" in file.permissions["read"]:
            mode[2] += 4
        mode = int("".join([str(x) for x in mode]))

        nlink = 0
        uid = file.owner
        gid = file.group_owner
        size = file.size
        # TODO: Implement atime, mtime, and ctime
        atime = 0
        mtime = 0
        ctime = 0
        path = file.pwd()

        stat_result = stat_struct(is_file, mode, nlink, uid, gid, size, atime, mtime, ctime, path)

        return Result(success=True, data=stat_result)

    def sys_mkdir(self, pathname: str, mode: int) -> Result:
        """
        Make a directory

        Args:
            pathname (str): The path of the directory to make
            mode (int): Octal permissions of the new `Directory`

        Returns:
            Result: A `Result` object with the success flag set accordingly and the data flag containing the new `Directory` object if successful
        """
        # Make sure it doesn't already exist
        find_dir = self.fs.find(pathname)

        if find_dir.success:
            return Result(success=False, message=ResultMessages.ALREADY_EXISTS)

        if "/" not in pathname:
            pathname = "./" + pathname

        # Make sure we have write permissions on the parent dir
        parent_path = "/".join(pathname.split("/")[:-1])

        # Just in case
        find_parent = self.fs.find(parent_path)

        if not find_parent.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        if not find_parent.data.check_perm("write", self).success:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED_WRITE)

        new_dir = Directory(pathname.split("/")[-1], find_parent.data, owner=self.sys_getuid(),
                            group_owner=self.sys_getgid())

        add_file = find_parent.data.add_file(new_dir)

        if not self.sys_chmod(pathname, mode).success:
            # rwxr-xr-x
            new_dir.permissions = {"read": ["owner", "group", "public"], "write": ["owner"],
                                   "execute": ["owner", "group", "public"]}

        if not add_file.success:
            return Result(success=False, message=ResultMessages.GENERIC)

        return Result(success=True, data=new_dir)

    def sys_chmod(self, pathname: str, mode: int) -> Result:
        """
        Change the permission mode of a `File`/`Directory`

        Args:
            pathname (str): File path of the `File`/`Directory` to change mode of
            mode (int): Octal permissions of the given pathname

        Returns:
            Result: A `Result` instance with the `success` flag set accordingly.
        """
        find_file = self.fs.find(pathname)

        if not find_file.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        # TODO: Allow changing setuid bit

        if self.sys_getuid() not in [find_file.data.owner, 0]:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

        raw_mode = str(bin(mode)).replace("0b", "")
        raw_mode = "0" * (9 - len(raw_mode)) + raw_mode

        chmod_bits = []
        for x in range(0, len(raw_mode), 3):
            chmod_bits.append(raw_mode[x: x + 3])

        perms = {"read": [], "write": [], "execute": []}

        for x in range(3):
            bits = chmod_bits[x]
            scope = ["owner", "group", "public"][x]

            for y in range(3):
                bit = bits[y]
                perm_scope = ["read", "write", "execute"][y]

                if bit == "1":
                    perms[perm_scope].append(scope)

        find_file.data.permissions = perms
        find_file.data.handle_event("change_perm")
        return Result(success=True)

    def sys_creat(self, pathname: str, mode: int) -> Result:
        """
        Make a file

        Args:
            pathname (str): The path of the file to make
            mode (int): Octal permissions of the new `File`

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        # Try to resolve the path
        find_file = self.fs.find(pathname)

        if find_file.success:
            return Result(success=False, message=ResultMessages.ALREADY_EXISTS)

        if "/" not in pathname:
            pathname = "./" + pathname

        # Make sure we have write permissions on the parent dir
        parent_path = "/".join(pathname.split("/")[:-1])

        # Just in case
        find_parent = self.fs.find(parent_path)

        # Sanity check
        if not find_parent.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        # We need write permissions on the parent
        if not find_parent.data.check_perm("write", self).success:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

        new_file = File(pathname.split("/")[-1], "", find_parent.data, self.sys_getuid(), self.sys_getgid())
        self.sys_chmod(pathname, mode)
        find_parent.data.add_file(new_file)

        return Result(success=True)

    def sys_rename(self, oldpath: str, newpath: str) -> Result:
        """
        Rename or move a file or directory

        Args:
            oldpath (str): The original file/directory path to rename
            newpath (str): The new path of the file/directory

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        find_old = self.fs.find(oldpath)

        if not find_old.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        if not find_old.data.check_owner(self).success or self.sys_getuid() != 0:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

        copy_result = copy(self, oldpath, newpath)

        if not copy_result.success:
            return copy_result

        # Rename means move, so delete the original
        delete_result = self.fs.find(oldpath).data.delete(self)

        if not delete_result.success:
            return delete_result

        return Result(success=True)

    def sys_exit(self, force=False) -> None:
        """
        Exit a session and return to the previous session. If a previous computer exists and no sessions exist,
        return to the previous computer. If no previous computer exists, exit the game.

        Args:
            force (bool): If a prev computer exists, exit to previous computer regardless of previous sessions. If no previous computers exist, exit the game.

        Returns:
            None
        """
        if force:
            if len(self.shell.computers) == 1:
                self.save()
                exit(0)
            else:
                self.sessions = []
                self.shell.computers.pop()
        else:
            if len(self.shell.computers) == 1:
                if len(self.sessions) == 1:
                    self.save()
                    exit(0)
                else:
                    self.sessions.pop()
            else:
                self.shell.computers.pop()

    def sys_reboot(self, mode: int) -> Result:
        """
        Simulate a computer reboot. Clear all sessions and re-initialize the machine

        Args:
            mode (int: Bitwise flags of the operation to take

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        if self.sys_getuid() != 0:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

        if RebootMode.LINUX_REBOOT_CMD_POWER_OFF in mode:
            self.sys_exit(True)

        if RebootMode.LINUX_REBOOT_CMD_RESTART in mode:
            print(f"Rebooting...")
            sleep(1)
            if system() == "Windows":
                real_syscall("cls")
            else:
                real_syscall("clear")
            self.run_command("clear", [], pipe=True)
            self.init()
            while len(self.sessions) != 1:
                self.sys_exit()

        return Result(success=True)

    def sys_rmdir(self, pathname: str) -> Result:
        """
        Remove an empty directory

        Args:
            pathname (str): The file path of the empty `Directory` to remove

        Returns:
            Result: A `Result` object with the success flag set accordingly
        """
        find_result = self.fs.find(pathname)

        if not find_result.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        if find_result.data.is_file():
            return Result(success=False, message=ResultMessages.IS_FILE)

        if len(find_result.data.files) > 0:
            return Result(success=False, message=ResultMessages.NOT_EMPTY)

        delete_response = find_result.data.delete(self)

        if not delete_response.success:
            return delete_response

        return Result(success=True)

    def sys_execv(self, pathname: str, argv: list) -> Result:
        """
        Execute a file

        Args:
            pathname (str): The path name of the binary to execute
            argv (list): A list of arguments to pass to the binary

        Returns:
            Result: A `Result` arguments containing the output from the binary
        """
        find_result = self.fs.find(pathname)

        if not find_result.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        if not find_result.data.check_perm("execute", self).success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        return self.run_command(pathname.split("/")[-1], argv, False)

    def sys_execvp(self, command: str, argv: list) -> Result:
        """
        Execute a command using the PATH rather than the full binary path. Does exactly what the system shell does.

        Args:
            command (str): The command to run
            argv (list): A list of arguments to pass to the binary

        Returns:
            Result: A `Result` arguments containing the output from the binary
        """
        return self.run_command(command, argv, False)

    def sys_unlink(self, pathname: str) -> Result:
        """
        Removes a link to a file. If there are no links left, the file is removed.

        Args:
            pathname (str): The file path of the `File` to unlink

        Returns:
            Result: A `Result` arguments containing the output from the binary

        """
        find_result = self.fs.find(pathname)

        if not find_result.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        if not find_result.data.check_perm("write", self) or not find_result.data.check_perm("execute", self):
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

        delete_result = find_result.data.delete(self)

        if not delete_result.success:
            return delete_result

        return Result(success=True)


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

    def dhcp(self, subnet: int) -> Result:
        """
        Distributes IP addresses to clients on the network

        Args:
            subnet (int): subnet id to assign the client to

        Returns:
            Result: A `Result` with the `success` flag set accordingly. The `data` flag contains the IP to assign to a given client.
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
            return Result(success=False, message=ResultMessages.EMPTY)

        # Choose a random ip from the pool
        ip = choice(self.ip_pool[subnet])

        # Remove the IP from the pool since it's in use
        self.ip_pool[subnet].remove(ip)
        return Result(success=True, data=ip)

    def find_client(self, host: str, port: int) -> Result:
        # Check if the given `host` belongs to us or its in an external lan
        prefix = ".".join(self.lan.split(".")[0:2]) + "."
        subnet = host.split(".")[2]

        if host == self.wan:
            if port in self.port_forwarding.keys():
                return Result(success=True, data=self.port_forwarding[port].services[port])
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        # We're finding one of our own
        if host.startswith(prefix):
            # Quick check, if subnet is empty, we don't have the client
            get_subnet = self.clients.get(int(subnet))
            if not get_subnet:
                return Result(success=False, message=ResultMessages.NOT_FOUND)
            # We can ignore the port because we don't need port forwarding in a lan
            client_result = next((x for x in get_subnet.values() if x.lan == host), None)
            if not client_result:
                return Result(success=False, message=ResultMessages.NOT_FOUND)

            # Now we need to check if the client has a service on that port
            # In real life, we wouldn't be able to make a connection if there is no service
            # on the given port
            if port not in client_result.services.keys():
                return Result(success=False, message=ResultMessages.NOT_FOUND)

            return Result(success=True, data=client_result.services.get(port))

        # We need to get the client from another lan, ask the ISP to handle it
        return self.parent.find_client(host, port)

    def add_new_client(self, client: Computer, subnet: int = 1) -> Result:
        """
        Connect a given `Computer` to the given `Router`'s LAN.
        Also, assign an IP address using the `dhcp()` function.

        Args:
            client (:obj:`Computer`): The `Computer` instance to connect to the `Router`'s LAN
            subnet (int, optional): The subnet id to assign the given `Computer` to

        Returns:
            Result: A `Result` with the `success` flag set accordingly. The `data` flag contains the `client`'s newly assigned IP address if successful.
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

        return Result(success=True, data=client.lan)


class ISPRouter(Router):
    def __init__(self):
        """
        An ISP router is just a router of routers
        """
        super().__init__()
        self.wan = "1.1.1.1"
        self.used_ips = ["1.1.1.1"]

    def dhcp(self, **kwargs) -> Result:
        """
        Distributes IP addresses to clients on the network

        Returns:
            Result: A `Result` with the `success` flag set accordingly. The `data` flag contains the IP to assign to a given client.
        """
        while True:
            ip = ".".join(str(choice([x for x in range(1, 256) if x not in [192, 168]])) for _ in range(4))
            if ip not in self.used_ips:
                self.used_ips.append(ip)
                return Result(success=True, data=ip)

    def add_new_client(self, client: Router, **kwargs) -> Result:
        """
        Connect a given `Computer` to the given `ISPRouter`
        Also, assign an IP address using the `dhcp()` function.

        Args:
            client (:obj:`Computer`): The `Computer` instance to connect to the `ISPRouter`

        Returns:
            Result: A `Result` with the `success` flag set accordingly. The `data` flag contains the `client`'s newly assigned IP address if successful.
        """
        dhcp_result = self.dhcp()
        if dhcp_result.success:
            client.wan = dhcp_result.data
            client.parent = self
            self.clients[client.wan] = client
            return Result(success=True, data=client.wan)
        else:
            # Failed for some reason (DHCP will give us our error)
            return dhcp_result

    def find_client(self, host: str, port: int) -> Result:
        if host == self.wan:
            if port in self.services.keys():
                return Result(success=True, data=self.services.get(port))
            else:
                return Result(success=False, message=ResultMessages.NOT_FOUND)
        else:
            find_client = next((x for x in self.clients.values() if x.wan == host), None)

            if find_client:
                return find_client.find_client(host, port)
