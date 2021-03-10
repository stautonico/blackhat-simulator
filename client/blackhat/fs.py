import sys
from random import choice
from string import ascii_uppercase, digits
from typing import Optional, Dict, List, Literal, Union

from .helpers import SysCallStatus, SysCallMessages


class FSBaseObject:
    def __init__(self, name: str, parent: Optional["Directory"], owner: int, group_owner: int) -> None:
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
        """imt: Changed time; when the file"s metadata was last changed (ex. perms)"""

    def is_directory(self) -> bool:
        return type(self) == Directory

    def is_file(self) -> bool:
        return type(self) == File

    def check_perm(self, perm: Literal["read", "write", "execute"], uid: int) -> SysCallStatus:
        # If we"re root (UID 0), return True because root has all permissions
        if uid == 0:
            return SysCallStatus(success=True)
        # If "public", don"t bother checking anything else
        if "public" in self.permissions[perm]:
            return SysCallStatus(success=True)

        # TODO: Implement groups and check group permissions

        if "owner" in self.permissions[perm]:
            if self.owner == uid:
                return SysCallStatus(success=True)

        # No permission
        return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED)

    def change_owner(self, caller: int, new_owner: int) -> SysCallStatus:
        # Only the current owner and root are allowed to change the files owner
        if caller == self.owner or caller == 0:
            self.owner = new_owner
            return SysCallStatus(success=True)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED)


class File(FSBaseObject):
    def __init__(self, name: str, content: str, parent: "Directory", owner: int, group_owner: int) -> None:
        super().__init__(name, parent, owner, group_owner)
        self.content = content
        self.size = sys.getsizeof(self.name + self.content)

    def read(self, caller: int) -> SysCallStatus:
        if self.check_perm("read", caller).success:
            return SysCallStatus(success=True, data=self.content)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED)

    def write(self, caller: int, data: str) -> SysCallStatus:
        if self.check_perm("write", caller).success:
            self.content = data
            self.update_size()
            return SysCallStatus(success=True)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED)

    def append(self, caller: int, data: str) -> SysCallStatus:
        # NOTE: This may be unnecessary, we"ll find out later
        if self.check_perm("write", caller).success:
            self.content += data
            self.update_size()
            return SysCallStatus(success=True)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED)

    def update_size(self) -> None:
        self.size = sys.getsizeof(self.name + self.content)

        # First, update our own size
        self.size = sys.getsizeof(self.content + self.name)
        # Now, recursively update our parent"s size
        if self.parent:
            self.parent.update_size()


class Directory(FSBaseObject):
    def __init__(self, name: str, parent: Optional["Directory"], owner: int, group_owner: int):
        super().__init__(name, parent, owner, group_owner)
        self.files = {}
        self.size = None

        self.update_size()

    def add_file(self, file: Union[File, "Directory"]) -> SysCallStatus:
        if file.name in self.files.keys():
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

        self.files[file.name] = file
        self.update_size()
        return SysCallStatus(success=True)

    def calculate_size(self) -> int:
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
        return self.files.get(filename, None)

    def update_size(self) -> None:
        self.size = self.calculate_size()

        # This does the same as the file update size. Updates its own size
        # Then the parent updates its size, taking into account selfs new size
        # Like a chain until all parent folders have been updated

        if self.parent:
            self.parent.update_size()


class StandardFS:
    def __init__(self, computer) -> None:
        self.computer = computer

        # The filesystem root (/) (owned by root)
        self.files = Directory("/", None, 0, 0)

        self.init()

    def init(self) -> None:
        # Setup the directory structure in the file system (Unix FHS)
        for dir in ["bin", "etc", "home", "lib", "root", "tmp", "usr", "var"]:
            directory = Directory(dir, self.files, 0, 0)
            # Special case for /tmp (read and write by everyone)
            if dir == "tmp":
                directory.permissions = {"read": ["owner", "group", "public"], "write": ["owner", "group", "public"],
                                         "execute": []}
            else:
                # TODO: Change this to be more accurate
                # (rwx rw- r--)
                directory.permissions = {"read": ["owner", "group", "public"], "write": ["owner", "group"],
                                         "execute": ["owner"]}

            self.files.add_file(directory)

        # Individually setup each directory in the root
        # self.setup_bin()
        self.setup_etc()
        # self.setup_home()
        # self.setup_lib()
        self.setup_root()
        # self.setup_tmp()
        self.setup_usr()
        self.setup_var()

    def setup_etc(self) -> None:
        etc_dir: Directory = self.files.find("etc")
        # Create the /etc/passwd file
        # The passwd file should have roots creds (bc root is created before the file)
        passwd_file: File = File("passwd", f"root:{self.computer.users['root'].password}\n", etc_dir, 0, 0)
        etc_dir.add_file(passwd_file)

        # /etc/skel (home dir template)
        skel_dir: Directory = Directory("skel", etc_dir, 0, 0)

        for dir in ["Desktop", "Documents", "Downloads", "Music", "Pictures", "public", "Templates", "Videos"]:
            current_dir = Directory(dir, skel_dir, 0, 0)
            current_dir.permissions = {"read": ["owner", "group", "public"], "write": ["owner"],
                                       "execute": []}
            skel_dir.add_file(current_dir)

        # /etc/skel/.shellrc (.bashrc/.zshrc equivalent)
        skel_dir.add_file(File(".shellrc", "", skel_dir, 0, 0))

        etc_dir.add_file(skel_dir)

        # /etc/hostname (holds system hostname)
        # Stupid windows style default hostnames
        new_hostname = f"DESKTOP-{''.join([choice(ascii_uppercase + digits) for _ in range(7)])}"
        etc_dir.add_file(File("hostname", new_hostname, etc_dir, 0, 0))

    def setup_root(self) -> None:
        # Create /root/.shellrc
        root_dir: Directory = self.files.find("root")

        root_shellrc: File = File(".shellrc", "export HOME=/root", root_dir, 0, 0)
        root_dir.add_file(root_shellrc)

    def setup_usr(self) -> None:
        # Setup /usr/share
        usr_dir: Directory = self.files.find("usr")

        share_dir: Directory = Directory("share", usr_dir, 0, 0)
        usr_dir.add_file(share_dir)

        # /usr/share/man (stores man pages from __DOC__)
        man_dir: Directory = Directory("man", share_dir, 0, 0)
        share_dir.add_file(man_dir)

        # TODO: Loop through all binaries and create a manpage using the __DOC__ var

    def setup_var(self) -> None:
        # This should exist at runtime
        var_dir: Directory = self.files.find("var")

        # Create /var/log
        log_dir: Directory = Directory("log", var_dir, 0, 0)
        # mv log -> var
        var_dir.add_file(log_dir)

        # Create the `syslog` in /var/log
        log_dir.add_file(File("syslog", "", log_dir, 0, 0))
