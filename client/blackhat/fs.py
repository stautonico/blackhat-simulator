import importlib
import os
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

    def pwd(self) -> str:
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

    def delete(self, caller) -> SysCallStatus:
        if self.parent:
            # In unix, we need read+write permissions to delete
            if self.check_perm("read", caller).success and self.check_perm("write", caller).success:
                del self.parent.files[self.name]
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

    # TODO: REFRACTOR
    def copy(self, dst, user, root_user, computer, copy_perms=False, verbose=False):

        # Find the file to see if it exists first
        if "/" not in dst:
            dst = "./" + dst

        found_file = find(computer, dst)
        new_file_name = None

        if not found_file["success"]:
            # Try to find it (parent folder)
            found_file = find(computer, "/".join(dst.split("/")[:-1]))
            if not found_file["success"]:
                return {"success": False, "message": "not found"}

        to_write = found_file["file"]

        if dst.split("/")[-1] != to_write.name:
            new_file_name = dst.split("/")[-1]

        if to_write.is_file():
            # If its a file, we're overwriting
            # Check the permissions (write to `copy_to_dir + file` and read from `self`)
            # Check read first (split for error messages)
            if not self.check_perm("read", user, root_user):
                return {"success": False, "message": "not allowed read file"}
            else:
                if not to_write.check_perm("write", user, root_user):
                    return {"success": False, "message": "not allowed write"}
                else:
                    to_write.write(self.content)
                    to_write.owner = user
                    to_write.group_owner = user.groups[user.username]
        else:
            # Its a dir, so its a new file
            if not self.check_perm("read", user, root_user):
                return {"success": False, "message": "not allowed read file"}
            else:
                if not to_write.check_perm("write", user, root_user):
                    return {"success": False, "message": "not allowed write"}
                else:
                    new_filename = new_file_name or self.name
                    new_file = File(new_filename, self.content, to_write, user, user.groups[user.username])
                    to_write.add_file(new_file)
                    # We have to do this so the permissions work no matter if we're overwriting or not
                    to_write = new_file

        if verbose:
            print(f"'{src.name}' -> '{dst}'")

        if copy_perms:
            to_write.permissions = self.permissions

        return {"success": True, "message": ""}




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
        self.setup_bin()
        self.setup_etc()
        # self.setup_home()
        # self.setup_lib()
        self.setup_root()
        # self.setup_tmp()
        self.setup_usr()
        self.setup_var()

    def setup_bin(self) -> None:
        bin_dir: Directory = self.files.find("bin")

        for file in os.listdir("./blackhat/bin"):
            # Ignore the __init__.py and __pycache__ because those aren't bins (auto generated)
            if file not in ["__init__.py", "__pycache__"]:
                current_file = File(file.replace(".py", ""), "[BINARY DATA]", bin_dir, 0, 0)
                with open(f"./blackhat/bin/{file}", "r") as f:
                    current_file.size = sys.getsizeof(f.read()) / 32
                    current_file.permissions = {"read": ["owner", "group", "public"], "write": ["owner"],
                                                "execute": ["owner", "group", "public"]}

                bin_dir.add_file(current_file)

    def setup_etc(self) -> None:
        etc_dir: Directory = self.files.find("etc")
        # Create the /etc/passwd file
        # The passwd file should have roots creds (bc root is created before the file)
        passwd_file: File = File("passwd", f"root:{self.computer.users[0].password}\n", etc_dir, 0, 0)
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

        # Loop through all the files in /bin and check if they have a __DOC__.
        for binary in self.files.find("bin").files.keys():
            try:
                module = importlib.import_module(f"blackhat.bin.{binary}")
                current_manpage = File(binary, module.__DOC__, man_dir, 0, 0)
                man_dir.add_file(current_manpage)
            except AttributeError as e:
                pass

    def setup_var(self) -> None:
        # This should exist at runtime
        var_dir: Directory = self.files.find("var")

        # Create /var/log
        log_dir: Directory = Directory("log", var_dir, 0, 0)
        # mv log -> var
        var_dir.add_file(log_dir)

        # Create the `syslog` in /var/log
        log_dir.add_file(File("syslog", "", log_dir, 0, 0))

    def find(self, pathname: str) -> SysCallStatus:
        # Special cases
        # Replace '~' with $HOME (if exists)
        if self.computer.sessions[-1].env.get("HOME", ""):
            pathname = pathname.replace("~", self.computer.sessions[-1].env.get("HOME", ""))

        if pathname == "/":
            return SysCallStatus(success=True, data=self.files)

        if pathname == ".":
            return SysCallStatus(success=True, data=self.computer.sessions[-1].current_dir)

        if pathname == "..":
            # Check if the directory has a parent
            # If it doesn't, we can assume that we're at /
            # In the case of /, just return /
            if not self.computer.sessions[-1].current_dir.parent:
                return SysCallStatus(success=True, data=self.files)
            else:
                return SysCallStatus(success=True, data=self.computer.sessions[-1].current_dir.parent)

        if pathname == "...":
            # Check if the directory has a parent
            # If it doesn't, we can assume that we're at /
            # In the case of /, just return /
            # And then do it again (go back twice)
            if not self.computer.sessions[-1].current_dir.parent:
                return SysCallStatus(success=True, data=self.computer.fs.files)
            else:
                current_dir = self.computer.sessions[-1].current_dir.parent
                if current_dir.parent:
                    return SysCallStatus(success=True, data=current_dir.parent)
                else:
                    return SysCallStatus(success=True, data=self.computer.fs.files)

        # Regular (non-special cases)
        pathname = pathname.split("/")
        # Check if `pathname` is absolute or relative
        # Check if the first arg is empty (because we split by /) which means the first arg is empty if it was a "/"
        if pathname[0] == "":
            # Absolute (start at root dir)
            current_dir = self.files
        else:
            # Relative (based on current dir)
            current_dir = self.computer.sessions[-1].current_dir

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
                    return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        # This only runs when we successfully found
        return SysCallStatus(success=True, data=current_dir)
