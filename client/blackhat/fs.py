import datetime
import importlib
import os
import sys
from random import choice
from string import ascii_uppercase, digits
from typing import Optional, Dict, List, Literal, Union, Callable

from colorama import Style

from .helpers import Result, ResultMessages

event_types = Literal["read", "write", "move", "change_perm", "change_owner", "delete"]


class FSBaseObject:
    def __init__(self, name: str, parent: Optional["Directory"], owner: int, group_owner: int) -> None:
        """
        The base object that contains info shared between `Directories` and `Files`

        Args:
            name (str): The name of the `File`/`Directory`
            parent (Directory): The `Directory` one level up the tree
            owner (int): The UID of the owner of the `File`/`Directory`
            group_owner (int): The GID of the owner of the `File`/`Directory`
        """
        self.name: str = name
        self.permissions: Dict[str, List[Literal["read", "write", "execute"]]] = {"read": ["owner", "group", "public"],
                                                                                  "write": ["owner"],
                                                                                  "execute": []}
        """Permissions for accessing the file. Default permissions; rw-r--r-- (644)"""
        self.parent: Optional["Directory"] = parent
        self.owner: int = owner
        self.group_owner: int = group_owner
        self.link_count: int
        self.size: int
        self.atime: int  # Last access time (unix time stamp)
        """int: Access time; when file was last read from/accessed"""
        self.mtime: int  # Last modified time (unix time stamp)
        """int: Modified time; when the file"s content was last modified"""
        self.ctime: int  # Last file status change (unix time stamp)
        """int: Changed time; when the file"s metadata was last changed (ex. perms)"""
        self.events: Dict[event_types, Callable] = {}

    def is_directory(self) -> bool:
        """
        Determines if a given item is a `Directory`

        Returns:
            bool: `True` if the given item is a `Directory` otherwise `False`
        """
        return type(self) == Directory

    def is_file(self) -> bool:
        """
        Determines if a given item is a `File`

        Returns:
            bool: `True` if the given item is a `File` otherwise `False`
        """
        return type(self) == File

    def check_perm(self, perm: Literal["read", "write", "execute"], computer) -> Result:
        """
        Checks if the current user has the given `perm`

        Args:
            perm (str): The permission to check ("read", "write", "execute")
            computer: The current `Computer` instance

        Returns:
            Result: A `Result` object with the `success` flag set accordingly
        """
        # If we"re root (UID 0), return True because root has all permissions
        if computer.sys_getuid() == 0:
            return Result(success=True)
        # If "public", don"t bother checking anything else
        if "public" in self.permissions[perm]:
            return Result(success=True)

        if "group" in self.permissions[perm]:
            if self.group_owner in computer.get_user_groups(computer.sys_getuid()).data:
                return Result(success=True)

        if "owner" in self.permissions[perm]:
            if self.owner == computer.sys_getuid():
                return Result(success=True)

        # No permission
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    def check_owner(self, computer) -> Result:
        """
        Checks if the given UID or GID is one of the owners (for chmod/chgrp/etc)

        Args:
            computer: The current `Computer` instance

        Returns:
            Result: A `Result` object with the `success` flag set accordingly
        """
        # Get the list of user's groups
        groups = computer.get_user_groups(computer.sys_getuid()).data

        if self.owner == computer.sys_getuid() or self.group_owner in groups:
            return Result(success=True)
        else:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    def change_owner(self, computer, new_user_owner: Optional[int] = None,
                     new_group_owner: Optional[int] = None) -> Result:
        """
        Change the owner (user and/or group) of a given `File`/`Directory`, but check if the given UID should be allowed to first

        Args:
            computer: The current `Computer` instance
            new_user_owner (int): The UID of the new owner (user) of the `File`/`Directory`
            new_group_owner (int): The GID of the new owner (group) of the `File`/`Directory`

        Returns:
            Result: A `Result` with the `success` flag set accordingly
        """
        caller_groups = computer.get_user_groups(computer.sys_getuid()).data
        # Check if the owner or group owner is correct or if we're root
        if computer.sys_getuid() == self.owner or self.group_owner in caller_groups or computer.sys_getuid() == 0:
            # We need at least one of the two params (uid/gid)
            # Using `if not new_user_owner/not new_group_owner` won't work because `not 0` (root group) == True (???)
            if new_user_owner is None and new_group_owner is None:
                return Result(success=False, message=ResultMessages.MISSING_ARGUMENT)
            else:
                # Same thing with uid 0
                if new_user_owner is not None:
                    # Confirm that the user exists
                    if computer.get_user(uid=new_user_owner).success:
                        self.owner = new_user_owner
                    else:
                        return Result(success=False, message=ResultMessages.NOT_FOUND)

                # Confirm that the new group exists
                # Same thing with gid 0
                if new_group_owner is not None:
                    # Confirm that the user exists
                    if computer.get_group(gid=new_group_owner).success:
                        self.group_owner = new_group_owner
                    else:
                        return Result(success=False, message=ResultMessages.NOT_FOUND)

                self.handle_event("change_owner")
                return Result(success=True)
        else:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    def pwd(self) -> str:
        """
        Get the full path of the `File` in the file system

        Returns:
            str: A complete file path starting at / (root)
        """
        current_dir = self
        working_dir = []

        while True:
            # Check if we're at /
            working_dir.append(current_dir.name)
            if not current_dir.parent:
                break
            current_dir = current_dir.parent

        working_dir.reverse()
        working_dir = "/".join(working_dir)
        # Try to remove double slash
        if working_dir.startswith("//"):
            working_dir = working_dir[1:]

        return working_dir

    def delete(self, computer) -> Result:
        """
        Check if the `caller` has the proper permissions to delete a given file, then remove it

        Args:
            computer: The current computer object

        Returns:
            Result: A `Result` object with the `success` flag set accordingly
        """
        if self.parent:
            # In unix, we need read+write permissions to delete
            if self.check_perm("read", computer).success and self.check_perm("write", computer).success:
                self.handle_event("delete")
                del self.parent.files[self.name]
                return Result(success=True)
            else:
                return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    def add_event_listener(self, event: event_types, function: Callable, when: Literal["before", "after"] = "after"):
        """
        Bind a function to run whenever a given event fires.
        A `FSBaseObject` can only have one function per event type.
        If a function is already bound to the given event type, it will be overwritten.

        Args:
            event: The given event type to bind the given `function` to.
            Valid event types include: `read`, `write`, `move`, `perm`, `delete`
            <ul>
                <li>read - When a file is read from</li>
                <li>write - When a file is written to</li>
                <li>move - When a file is moved to a different location AKA: When a file's parent folder changes</li>
                <li>perm - When a file's owner, group owner, or permissions changes</li>
                <li>delete - Before a file is deleted</li>
            </ul>
            function: The function/method to be called when the given `event` is fired
            when (str): When the event is fired (for example, before the read happens, or after)

        Returns:
             Result: A `Result` with the `success` flag set accordingly.
        """
        self.events[event] = function
        return Result(success=True)

    def remove_event_listener(self, event: event_types):
        """
        Unbinds the current function from the given `event` type

        Args:
            event: The event type to unbind. Valid event types include: `read`, `write`, `move`, `perm`, `delete`

        Returns:
             Result: A `Result` with the `success` flag set accordingly.
        """
        try:
            self.events.pop(event)
        except Exception:
            pass

        return Result(success=True)

    def handle_event(self, event: event_types):
        """
        Handles executing the function bound to the given `event`

        Args:
            event: The event type to run. Valid event types include: `read`, `write`, `move`, `perm`, `delete`

        Returns:
             Result: A `Result` with the `success` flag set accordingly.
        """
        if event in self.events.keys():
            self.events[event](self)

        return Result(success=True)


class File(FSBaseObject):
    def __init__(self, name: str, content: str, parent: "Directory", owner: int, group_owner: int) -> None:
        """
        The class object representing a file in the file system

        Args:
            name (str): The name of the given `File`
            content (str): The content within the given file. May be blank (empty string)
            parent (Directory): The `Directory` one level up the tree
            owner (int): The UID of the owner of the `File`/`Directory`
            group_owner (int): The GID of the owner of the `File`/`Directory
        """
        super().__init__(name, parent, owner, group_owner)
        self.content = content
        self.size = sys.getsizeof(self.name + self.content)

    def read(self, computer) -> Result:
        """
        Check if the current UID has permission to read the content of the file. Afterwards, return the content if allowed

        Args:
            computer: The current `Computer` instance

        Returns: Result: A `Result` object with the `success` flag set and the `data` flag set with the  file's content if permitted
        """
        if self.check_perm("read", computer).success:
            self.handle_event("read")
            return Result(success=True, data=self.content)
        else:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    def write(self, data: str, computer) -> Result:
        """
        Check if the current UID has permission to write to the file. Update the file's contents if allowed

        Args:
            data (str): The new content to write to the `File`
            computer: The current `Computer` instance

        Returns:
            Result: A `Result` object with the `success` flag accordingly
        """
        if self.check_perm("write", computer).success:
            self.content = data
            self.update_size()
            self.handle_event("write")
            return Result(success=True)
        else:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    def append(self, data: str, computer) -> Result:
        """
        Check if the current UID has permission to write to the file. Append to the file's contents if allowed

        Args:
            data (str): The content to append to the `File`s current content
            computer: The current `Computer` instance

        Returns:
            Result: A `Result` object with the `success` flag accordingly
        """
        # NOTE: This may be unnecessary, we"ll find out later
        if self.check_perm("write", computer).success:
            self.content += data
            self.update_size()
            self.handle_event("write")
            return Result(success=True)
        else:
            return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    def update_size(self) -> None:
        """
        Calculates the size of the `File` and set in the object.
        Also, recursively tells it's parent to update its size.

        Returns:
            None
        """
        self.size = sys.getsizeof(self.name + self.content)

        # First, update our own size
        self.size = sys.getsizeof(self.content + self.name)
        # Now, recursively update our parent"s size
        if self.parent:
            self.parent.update_size()

    def __str__(self):
        return f"{self.name} - {self.owner}"


class Directory(FSBaseObject):
    def __init__(self, name: str, parent: Optional["Directory"], owner: int, group_owner: int):
        """
        The class object representing a directory within the file system

        Args:
            name (str): The name of the `File`/`Directory`
            parent (Directory): The `Directory` one level up the tree
            owner (int): The UID of the owner of the `File`/`Directory`
            group_owner (int): The GID of the owner of the `File`/`Directory`
        """
        super().__init__(name, parent, owner, group_owner)
        self.files = {}
        self.size = None

        self.update_size()

    def add_file(self, file: Union[File, "Directory"]) -> Result:
        """
        Add a new `File` or `Directory` to self's internal file map
        Also updates its size and triggers its parent to update their size

        Args:
            file (File/Directory): The `File`/`Directory` to add to self

        Returns:
            Result: A `Result` with the `success` flag set accordingly
        """
        if file.name in self.files.keys():
            return Result(success=False, message=ResultMessages.ALREADY_EXISTS)

        self.files[file.name] = file
        self.update_size()
        return Result(success=True)

    def calculate_size(self) -> int:
        """
        Calculate a total size for the given directory and (recursively) all its children (`File`(s)/`Directory`(ies))

        Returns:
            int: The total size (in bytes) of the given directory
        """
        total = 0

        for file in self.files.values():
            if file.is_directory():
                # Recursive
                total += file.calculate_size()
            else:
                if file.size:
                    total += file.size

        return total

    def find(self, filename: str) -> Optional[Union[File, "Directory"]]:
        """
        Find a `File` or `Directory` in self's internal file map

        Args:
            filename (str): The name of the `File`/`Directory` to find

        Returns:
            File or Directory or None: The `File` or `Directory` object if found, otherwise, None
        """
        return self.files.get(filename, None)

    def update_size(self) -> None:
        """
        Update self's size using `calculate_size()` then, triggers self's parent to update their size

        Returns:
            None
        """
        self.size = self.calculate_size()

        # This does the same as the file update size. Updates its own size
        # Then the parent updates its size, taking into account self's new size
        # Like a chain until all parent folders have been updated

        if self.parent:
            self.parent.update_size()


class StandardFS:
    def __init__(self, computer) -> None:
        """
        The class object representing a file system that belongs to a `Computer`

        Args:
            computer (Computer): The `Computer` that the given file system belongs to
        """
        self.computer = computer

        # The filesystem root (/) (owned by root)
        self.files = Directory("/", None, 0, 0)
        self.files.permissions = {"read": ["owner", "group", "public"],
                                  "write": ["owner", "group"],
                                  "execute": ["owner", "group", "public"]}

        self.init()

    def init(self) -> None:
        """
        All the functions required to setup a new filesystem

        Returns:
            None
        """
        # Setup the directory structure in the file system (Unix FHS)
        for dir in ["bin", "etc", "home", "lib", "root", "proc", "tmp", "usr", "var"]:
            directory = Directory(dir, self.files, 0, 0)
            # Special case for /tmp (read and write by everyone)
            if dir == "tmp":
                directory.permissions = {"read": ["owner", "group", "public"], "write": ["owner", "group", "public"],
                                         "execute": ["owner", "group", "public"]}
            elif dir == "proc":
                directory.permissions = {"read": ["owner", "group", "public"], "write": [],
                                         "execute": ["owner", "group", "public"]}
            else:
                # TODO: Change this to be more accurate
                # (rwx rw- r--)
                directory.permissions = {"read": ["owner", "group", "public"], "write": ["owner", "group"],
                                         "execute": ["owner", "group", "public"]}

            self.files.add_file(directory)

        # TODO: Replace all these with `mkdir -p` commands
        # NOTE: FS doesn't exist at this point so running commands might not be possible (since some commands need fs)
        # Individually setup each directory in the root
        self.setup_bin()
        self.setup_etc()
        # self.setup_home()
        # self.setup_lib()
        self.setup_proc()
        self.setup_root()
        # self.setup_tmp()
        self.setup_usr()
        self.setup_var()

    def setup_bin(self) -> None:
        """
        Read all the files in the `client.blackhat.bin` directory and create a virtual file in the fs.
        All these files represent binaries in the system

        Returns:
            None
        """
        bin_dir: Directory = self.files.find("bin")

        for file in os.listdir("./blackhat/bin"):
            # Ignore the __init__.py and __pycache__ because those aren't bins (auto generated)
            if file not in ["__init__.py", "__pycache__", "installable"]:
                current_file = File(file.replace(".py", ""), "[BINARY DATA]", bin_dir, 0, 0)
                try:
                    with open(f"./blackhat/bin/{file}", "r") as f:
                        current_file.size = sys.getsizeof(f.read()) / 32
                except IsADirectoryError:
                    current_file.size = 0

                current_file.permissions = {"read": ["owner", "group", "public"], "write": ["owner"],
                                            "execute": ["owner", "group", "public"]}

                bin_dir.add_file(current_file)

    def setup_etc(self) -> None:
        """
        Sets up:
        <ul>
            <li>/etc/passwd - Contains the username, hashed password, and UID of all the users in the system</li>
            <li>/etc/shadow - Contains the username, and hashed password of all users in the system</li>
            <li>/etc/groups - Contains the list of groups in the systems (name, GID)</li>
            <li>/etc/hostname - The hostname of the given `Computer`</li>
            <li>/etc/skel -  A "skeleton" needed to create a users home folder (located in /home/<USERNAME>)</li>
            <li>/etc/sudoers - The file that contains all of the sudo permissions</li>
            <li>/etc/apt/sources.list - Contains urls of apt repo servers</li>
        </ul>

        Returns:
            None
        """

        # EventHandler functions for /etc/passwd, /etc/shadow, and /etc/group
        def update_passwd(file):
            content = file.content.split("\n")

            for item in content:
                subitems = item.split(":")
                # An item in the list with a length of 1 or less are usually blank lines
                if len(subitems) > 1:
                    username, password, uid, primary_gid = subitems

                    try:
                        uid = int(uid)
                        primary_gid = int(primary_gid)
                    except Exception:
                        return

                    # Now we want to get the user by username
                    user_lookup = self.computer.get_user(username=username)

                    # If we don't find the user, that means we added a new user
                    if not user_lookup.success:
                        # Make sure no user has the uid
                        if not self.computer.get_user(uid=uid).success:
                            # Add the user
                            self.computer.add_user(username, password, uid, plaintext=False)
                            self.computer.add_group(name=username, gid=primary_gid)
                            self.computer.add_user_to_group(uid, primary_gid, "primary")
                    else:
                        # We have a user, now lets check if any of the data has changed
                        user = user_lookup.data

                        # If the password is 'x', that password is in the /etc/shadow file and should be ignored here
                        if user.password != password and password != "x":
                            result = self.computer.change_user_password(user.uid, password, plaintext=False)
                            if result.success:
                                user.password = password

                        if user.uid != uid:
                            result = self.computer.change_user_uid(user.uid, uid)
                            if result.success:
                                user.uid = uid

                        # If the GID changed, we want to:
                        # 1. Make sure the new GID exists
                        # 2. Remove the user's old primary gid membership
                        # 3. Add a the user to the new gid as primary
                        user_primary_gid = self.computer.get_user_primary_group(user.uid).data[0]

                        if user_primary_gid != primary_gid:
                            if self.computer.get_group(gid=primary_gid).success:
                                self.computer.remove_user_from_group(uid=user.uid, gid=user_primary_gid)
                                self.computer.add_user_to_group(user.uid, primary_gid, "primary")

                    # Will automatically remove incorrect changes
                    self.computer.sync_user_and_group_files()

        def update_shadow(file):
            content = file.content.split("\n")

            for item in content:
                subitems = item.split(":")
                # An item in the list with a length of 1 or less are usually blank lines
                if len(subitems) > 1:
                    username, password = subitems

                    # Now we want to get the user by username
                    user_lookup = self.computer.get_user(username=username)

                    # We have a user, now lets check if any of the data has changed
                    user = user_lookup.data

                    # If the password is 'x', that password is in the /etc/shadow file and should be ignored here
                    if user.password != password and password != "x":
                        result = self.computer.change_user_password(user.uid, password, plaintext=False)
                        if result.success:
                            user.password = password

                # Will automatically remove incorrect changes
                self.computer.sync_user_and_group_files()

        def update_group(file):
            content = file.content.split("\n")

            for item in content:
                subitems = item.split(":")
                # An item in the list with a length of 1 or less are usually blank lines
                if len(subitems) > 1:
                    group_name, password, gid, group_users = subitems

                    try:
                        uid = int(gid)
                    except Exception:
                        return

                    # Now we want to get the group by group name
                    group_lookup = self.computer.get_group(name=group_name)

                    # If we don't find the user, that means we added a new user
                    if not group_lookup.success:
                        # Make sure no group has the gid
                        if not self.computer.get_group(gid=gid).success:
                            # Add the group
                            self.computer.add_group(group_name, gid)
                            # TODO: Add users to the group by last param
                    else:
                        # We have a group, now lets check if any of the data has changed
                        group = group_lookup.data
                        # TODO: Add changes here

                    # Will automatically remove incorrect changes
                    self.computer.sync_user_and_group_files()

        etc_dir: Directory = self.files.find("etc")
        # Create the /etc/passwd file
        passwd_file: File = File("passwd", f"", etc_dir, 0, 0)

        passwd_file.add_event_listener("write", update_passwd)

        etc_dir.add_file(passwd_file)
        # Create the /etc/shadow file and change its perms (rw-------)
        shadow_file: File = File("shadow", f"", etc_dir, 0, 0)
        shadow_file.permissions = {"read": ["owner"], "write": ["owner"], "execute": []}
        shadow_file.add_event_listener("write", update_shadow)
        etc_dir.add_file(shadow_file)

        # Create the /etc/groups file
        group_file: File = File("group", f"root:x:0", etc_dir, 0, 0)
        group_file.add_event_listener("write", update_group)
        etc_dir.add_file(group_file)

        # /etc/skel (home dir template)
        skel_dir: Directory = Directory("skel", etc_dir, 0, 0)

        for dir in ["Desktop", "Documents", "Downloads", "Music", "Pictures", "Public", "Templates", "Videos"]:
            current_dir = Directory(dir, skel_dir, 0, 0)
            current_dir.permissions = {"read": ["owner", "group", "public"], "write": ["owner"],
                                       "execute": ["owner", "group", "public"]}
            skel_dir.add_file(current_dir)

        # /etc/skel/.shellrc (.bashrc/.zshrc equivalent)
        skel_dir.add_file(File(".shellrc", "", skel_dir, 0, 0))

        etc_dir.add_file(skel_dir)

        # /etc/hostname (holds system hostname)
        # Stupid windows style default hostnames (for fun, might change later)
        new_hostname = f"DESKTOP-{''.join([choice(ascii_uppercase + digits) for _ in range(7)])}"
        etc_dir.add_file(File("hostname", new_hostname, etc_dir, 0, 0))

        # /etc/sudoers (holds sudo permissions)
        # Sudoers has permissions r--r-----
        sudoers_file: File = File("sudoers", "root ALL=(ALL) ALL\n", etc_dir, 0, 0)
        sudoers_file.permissions = {"read": ["owner", "group"], "write": [], "execute": []}
        etc_dir.add_file(sudoers_file)

        # /etc/apt/sources.list
        apt_dir: Directory = Directory("apt", etc_dir, 0, 0)
        etc_dir.add_file(apt_dir)

        sources_file: File = File("sources.list", "", apt_dir, 0, 0)
        apt_dir.add_file(sources_file)

    def setup_proc(self) -> None:
        """
        Sets up:
        <ul>
            <li>/proc/uptime - Contains the amount of seconds since the system was booted</li>
        </ul>

        Returns:
            None
        """

        # EventHandler functions for /proc/uptime
        def update_uptime(file):
            file.content = str((datetime.datetime.now() - self.computer.boot_time).total_seconds())

        proc_dir: Directory = self.files.find("proc")
        # Create the /etc/passwd file
        uptime_file: File = File("uptime", f"", proc_dir, 0, 0)
        uptime_file.permissions = {"read": ["owner", "group", "public"], "write": [], "execute": []}

        uptime_file.add_event_listener("read", update_uptime, when="before")
        proc_dir.add_file(uptime_file)

    def setup_root(self) -> None:
        """
        Since the root user is different from a "standard" user, root's home folder needs to be setup separately.
        Otherwise, the format of root's home folder is the same as any other user

        Returns:
            None
        """
        # Create /root/.shellrc
        root_dir: Directory = self.files.find("root")

        root_shellrc: File = File(".shellrc", "export HOME=/root", root_dir, 0, 0)
        root_dir.add_file(root_shellrc)

    def setup_usr(self) -> None:
        """
        Sets up:
        <ul>
            <li>/usr/share/man - Contains all the "man pages", or instruction manuals, for all the system binaries</li>
            <li>/usr/bin - "Aftermarket" installed packages (apt) </li>
        </ul>

        Returns:
            None
        """
        # Setup /usr/share
        usr_dir: Directory = self.files.find("usr")

        share_dir: Directory = Directory("share", usr_dir, 0, 0)
        usr_dir.add_file(share_dir)

        # /usr/share/man
        man_dir: Directory = Directory("man", share_dir, 0, 0)
        share_dir.add_file(man_dir)

        self.generate_manpages()

        bin_dir: Directory = Directory("bin", usr_dir, 0, 0)
        usr_dir.add_file(bin_dir)

    def setup_var(self) -> None:
        """
        Sets up:
        <ul>
            <li>/var/log - Contains various log files</li>
            <li>/var/log/syslog - Logs various information about the given `Computer`</li>
            <li>/var/log/auth.log - Logs information about authentication attempts</li>
            <li>/var/lib/dpkg/status - The list of installed packages by apt</li>
            <li>/var/www/html - Default location for web content served by web servers</li>
        </ul>

        Returns:
            None
        """
        # This should exist at runtime
        var_dir: Directory = self.files.find("var")

        # Create /var/log
        log_dir: Directory = Directory("log", var_dir, 0, 0)
        # mv log -> var
        var_dir.add_file(log_dir)

        # Create the `syslog` in /var/log
        log_dir.add_file(File("syslog", "", log_dir, 0, 0))

        # Create /var/lib/dpkg/status
        lib_dir: Directory = Directory("lib", var_dir, 0, 0)
        var_dir.add_file(lib_dir)

        dpkg_dir: Directory = Directory("dpkg", lib_dir, 0, 0)
        lib_dir.add_file(dpkg_dir)

        status_file: File = File("status", "", dpkg_dir, 0, 0)
        dpkg_dir.add_file(status_file)

        # Create /var/www/html
        www_dir: Directory = Directory("www", var_dir, 0, 0)
        var_dir.add_file(www_dir)

        html_dir: Directory = Directory("html", www_dir, 0, 0)
        www_dir.add_file(html_dir)

    def find(self, pathname: str) -> Result:
        """
        Try to find a given file anywhere in the file system based on a given `pathname`

        Args:
            pathname (str): The full (absolute or relative) path of the file

        Returns:
            Result: A `Result` with the `success` flag set accordingly and the `data` flag with the found `File` or `Directory` if the file was found
        """

        # Special cases
        # Replace '~' with $HOME (if exists)
        get_home_env_var = self.computer.get_env("HOME")
        if get_home_env_var:
            pathname = pathname.replace("~", get_home_env_var)

        if pathname == "/":
            return Result(success=True, data=self.files)

        if pathname == ".":
            return Result(success=True, data=self.computer.sys_getcwd())

        if pathname == "..":
            # Check if the directory has a parent
            # If it doesn't, we can assume that we're at /
            # In the case of /, just return /
            if not self.computer.sys_getcwd().parent:
                return Result(success=True, data=self.files)
            else:
                return Result(success=True, data=self.computer.sys_getcwd().parent)

        if pathname == "...":
            # Check if the directory has a parent
            # If it doesn't, we can assume that we're at /
            # In the case of /, just return /
            # And then do it again (go back twice)0
            if not self.computer.sys_getcwd().parent:
                return Result(success=True, data=self.computer.fs.files)
            else:
                current_dir = self.computer.sys_getcwd().parent
                if current_dir.parent:
                    return Result(success=True, data=current_dir.parent)
                else:
                    return Result(success=True, data=self.computer.fs.files)

        # Regular (non-special cases)
        pathname = pathname.split("/")
        # Check if `pathname` is absolute or relative
        # Check if the first arg is empty (because we split by /) which means the first arg is empty if it was a "/"
        if pathname[0] == "":
            # Absolute (start at root dir)
            current_dir = self.files
        else:
            # Relative (based on current dir)
            current_dir = self.computer.sys_getcwd()

        # Filter out garbage
        while "" in pathname:
            pathname.remove("")

        for subdir in pathname:
            # Special case for current directory (.) (ignore it)
            if subdir == ".":
                continue

            # Special case for (..) (go to parent)
            elif subdir == "..":
                # Check if we're at the root
                if not current_dir.parent:
                    current_dir = self.files
                else:
                    current_dir = current_dir.parent

            else:
                current_dir = current_dir.find(subdir)
                if not current_dir:
                    return Result(success=False, message=ResultMessages.NOT_FOUND)

        # This only runs when we successfully found
        return Result(success=True, data=current_dir)

    def generate_manpages(self):
        find_man_dir = self.find("/usr/share/man")

        if not find_man_dir.success:
            return

        man_dir = find_man_dir.data

        find_usr_bin = self.find("/usr/bin")

        if not find_usr_bin.success:
            usr_bin = []
        else:
            usr_bin = list(find_usr_bin.data.files.keys())

        # Loop through all the files in /bin and run "parse_args()" with the `doc` set to `True`
        for binary in list(self.files.find("bin").files.keys()) + usr_bin:
            # Check if an manpage exist
            if not self.find(f"/usr/share/man/{binary}").success:
                try:
                    module = importlib.import_module(f"blackhat.bin.{binary}")
                except ImportError:
                    try:
                        module = importlib.import_module(f"blackhat.bin.installable.{binary}")
                    except ImportError:
                        continue

                try:
                    manpage = module.parse_args(args=[], doc=True).replace("**", Style.BRIGHT).replace("*/",
                                                                                                       Style.RESET_ALL)
                    manpage = manpage.removeprefix("\n").removesuffix("\n")
                    current_manpage = File(binary, manpage, man_dir, 0, 0)
                    man_dir.add_file(current_manpage)
                except AttributeError:
                    continue


def copy(computer, src_path: str, dst_path: str) -> Result:
    find_src = computer.fs.find(src_path)

    if not find_src.success:
        return Result(success=False, message=ResultMessages.NOT_FOUND)

    src = find_src.data

    # Handle file copying
    if src.is_file():
        # If the path is in the local dir
        if "/" not in dst_path:
            dst_path = "./" + dst_path

        try_find_dst = computer.fs.find(dst_path)

        # If the dst file doesn't exist, we can try to create a new item in the parent folder
        if not try_find_dst.success:
            # Try to find the destination file parent folder
            try_find_dst = computer.fs.find("/".join(dst_path.split("/")[:-1]))
            if not try_find_dst.success:
                return Result(success=False, message=ResultMessages.NOT_FOUND)

        to_write: Union[Directory, File] = try_find_dst.data

        # If we found the parent folder, set the filename to the parent folder
        if dst_path.split("/")[-1] != to_write.name:
            new_file_name = dst_path.split("/")[-1]
            if new_file_name == "":
                new_file_name = src.name
        else:
            new_file_name = src.name

        if to_write.is_file():
            # If its a file, we're overwriting
            # Check the permissions (write to `copy_to_dir + file` and read from `self`)
            # Check read first (split for error messages)
            if not src.check_perm("read", computer).success:
                return Result(success=False, message=ResultMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer).success:
                    return Result(success=False, message=ResultMessages.NOT_ALLOWED_WRITE)
                else:
                    to_write.write(src.content, computer)
                    to_write.owner = computer.sys_getuid()
                    to_write.group_owner = computer.sys_getgid()
        else:
            # If we have the parent dir, we need to create a new file
            if not src.check_perm("read", computer).success:
                return Result(success=False, message=ResultMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer).success:
                    return Result(success=False, message=ResultMessages.NOT_ALLOWED_WRITE)
                else:
                    new_filename = new_file_name
                    new_file = File(new_filename, src.content, to_write, computer.sys_getuid(), computer.sys_getgid())
                    new_file.events = src.events
                    to_write.add_file(new_file)
                    # We have to do this so the permissions work no matter if we're overwriting or not
                    to_write = new_file

        to_write.handle_event("move")
        return Result(success=True)
    # Handle directory copying
    else:
        # TODO: Refactor this to work in both cases instead of re-writing a ton of code
        # If the path is in the local dir
        if "/" not in dst_path:
            dst_path = "./" + dst_path

        try_find_dst = computer.fs.find(dst_path)

        # If the dst file doesn't exist, we can try to create a new item in the parent folder
        if not try_find_dst.success:
            # Try to find the destination file parent folder
            try_find_dst = computer.fs.find("/".join(dst_path.split("/")[:-1]))
            if not try_find_dst.success:
                return Result(success=False, message=ResultMessages.NOT_FOUND)

        to_write: Union[Directory, File] = try_find_dst.data

        # If we found the parent folder, set the filename to the parent folder
        if dst_path.split("/")[-1] != to_write.name:
            new_file_name = dst_path.split("/")[-1]
        else:
            new_file_name = src.name

        if new_file_name not in to_write.files:
            if not src.check_perm("read", computer):
                return Result(success=False, message=ResultMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer).success:
                    return Result(success=False, message=ResultMessages.NOT_ALLOWED_WRITE)
                else:
                    new_dir = Directory(new_file_name, to_write, computer.sys_getuid(), computer.sys_getgid())
                    new_dir.events = to_write.events
                    to_write.add_file(new_dir)
                    # Set a temporary write permission no matter what the new dir's permissions were so we can add its children
                    new_dir.permissions["write"] = ["owner"]
                    # Go through all the source's files and copy them into the new dir
                    for file in src.files.values():
                        response = copy(computer, file, new_dir.pwd())

                        if not response.success:
                            if response.message == ResultMessages.NOT_ALLOWED_READ:
                                return Result(success=False, message=ResultMessages.NOT_ALLOWED_READ)
                            elif response.message == ResultMessages.NOT_ALLOWED_WRITE:
                                return Result(success=False, message=ResultMessages.NOT_ALLOWED_WRITE)
        else:
            return Result(success=False, message=ResultMessages.ALREADY_EXISTS)

        new_dir.handle_event("move")
        return Result(success=True)

# TODO: Re-write the copy function so its not so shit


# def copy(computer, src_path: str, dst_path: str) -> Result:
#     # Make sure the src exists
#     find_src = computer.fs.find(src_path)
#
#     if "/" not in src_path:
#         src_path = "./" + src_path
#
#     src_filename = src_path.split("/")[-1]
#
#     if not find_src.success:
#         return Result(success=False, message=ResultMessages.NOT_FOUND)
#
#     # We need read permissions to copy
#     if not find_src.data.check_perm("read", computer).success:
#         return Result(success=False, message=ResultMessages.NOT_ALLOWED_READ)
#
#     if "/" not in dst_path:
#         dst_path = "/" + dst_path
#
#     find_dst = computer.fs.find(dst_path)
#
#     if not find_dst.success:
#         # Try to find the destination file parent folder
#         find_dst = computer.fs.find("/".join(dst_path.split("/")[:-1]))
#         if not find_dst.success:
#             return Result(success=False, message=ResultMessages.NOT_FOUND)
#
#     # We need write permissions of the dest
#     if not find_dst.data.check_perm("write", computer).success:
#         return Result(success=False, message=ResultMessages.NOT_ALLOWED_WRITE)
#
#     if find_src.data.is_file():
#         copy_file = File(src_filename, find_src.data.content, find_dst.data, find_src.data.owner,
#                          find_src.data.group_owner)
#     else:
#         copy_file = Directory(src_filename, find_dst.data, find_src.data.owner,
#                               find_src.data.group_owner)
#
#     find_dst.data.add_file(copy_file)
#
#     return Result(success=True)
