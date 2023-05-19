from typing import Optional, Dict, Union, Literal

from blackhat.fs import Permissions, EVENT_TYPE, EventCallback, Filesystem
from blackhat.fs.filesystems.ext4 import ext4_setup
from blackhat.util.result import Result, ResultMessage
from blackhat.util.time import Timestamp


class InodeBase:
    def __init__(self, name: str, owner: int, group_owner: int,
                 mode: Union[int, str] = None) -> None:
        self._name: str = name
        self._permissions: Permissions = Permissions(mode or 0o777)  # Possible exploit?

        # Parse the setuid from the mode
        self._setuid: bool = bool(mode & 0o4000)
        self._setgid: bool = bool(mode & 0o2000)
        self._sticky: bool = bool(mode & 0o1000)

        self._parent: Optional["Directory"] = None
        self._owner: int = owner
        self._group_owner: int = group_owner

        self._inode_number: int = 0
        self._link_count: int = 0
        self._size: int = 0  # In bytes
        self._block_count: int = 0  # In 4096 byte blocks (maybe change?)

        self._atime: Timestamp = Timestamp.from_timestamp(0, "ns")  # Last access time
        self._ctime: Timestamp = Timestamp.from_timestamp(0, "ns")  # Last inode change time
        self._mtime: Timestamp = Timestamp.from_timestamp(0, "ns")  # Last modification time
        self._crtime: Timestamp = Timestamp()  # Creation time (defaults to now)

        self._events: Dict[EVENT_TYPE, EventCallback] = {}

    # TODO: Implement "when" parameter (before or after)
    def add_event(self, type: EVENT_TYPE, callback: EventCallback):
        self._events[type] = callback

    @property
    def name(self) -> str:
        return self._name

    def is_directory(self) -> bool:
        """
        Check if this inode is a directory.
        :return: True if this inode is a directory, False otherwise.
        """
        return type(self) == Directory

    def is_file(self) -> bool:
        """
        Check if this inode is a file.
        :return: True if this inode is a file, False otherwise.
        """
        return type(self) == File

    def check_perm(self, perm: Literal[Permissions.READ, Permissions.WRITE, Permissions.EXECUTE],
                   user: int, group: int) -> bool:
        """
        Check if the given user has the given permission on this inode.
        :param perm: The permission to check for.
        :param user: The user to check for.
        :param group: The group to check for.
        :return: True if the user has the permission, False otherwise.
        """
        if user == self._owner:
            return self._permissions.user[perm]
        elif group == self._group_owner:
            return self._permissions.group[perm]
        else:
            return self._permissions.other[perm]

    def full_path(self):
        """
        Get the full path of this inode.
        :return: The full path of this inode.
        """
        if self._parent is None:
            return self._name
        else:
            return self._parent.full_path() + "/" + self._name


class File(InodeBase):
    def __init__(self, name: str, owner: int, group_owner: int,
                 mode: Union[str, int] = 0o644) -> None:
        super().__init__(name, owner, group_owner, mode)

        self._data: bytes = b""

    def read(self) -> Result[bytes]:
        # TODO: Insert fsuid or euid?
        if not self.check_perm(Permissions.READ, 0, 0):
            return Result(False, message=ResultMessage.FS.NOT_ALLOWED_READ)
        return Result(True, data=self._data)

    def write(self, data: bytes) -> Result[None]:
        if not self.check_perm(Permissions.WRITE, 0, 0):
            return Result(False, message=ResultMessage.FS.NOT_ALLOWED_WRITE)
        self._data = data
        # Call all the write events
        for event in self._events.get(EVENT_TYPE.WRITE, []):
            event(self, self)
        return Result(True, data=None)


class Directory(InodeBase):
    def __init__(self, name: str, owner: int, group_owner: int,
                 mode: Union[str, int] = 0o755) -> None:
        super().__init__(name, owner, group_owner, mode)

        self._children: Dict[str, InodeBase] = {}

    def add_child(self, child: InodeBase):
        child._parent = self
        self._children[child.name] = child

    def get_child(self, name: str) -> Optional[InodeBase]:
        return self._children.get(name, None)


class Ext4(Filesystem):
    def __init__(self):
        super().__init__()

        self._root: Directory = Directory("/", 0, 0, 0o755)
        self._current_directory: Directory = self._root

    def find(self, path) -> Result[Union[File, Directory]]:
        # Remove the mapped path from the beginning of our path to find
        # TODO: Make it that the filesystem can be mounted in several places at once
        path = path[len(self._mapped_path):]

        split_path = path.split("/")

        # FIXME: If any find issue arise, this is it. Probably something to do with empty paths

        if split_path[0] == "":
            split_path = split_path[1:]

        # Special case for root
        if path == self._mapped_path:
            return Result(True, data=self._root)

        current = self._root
        for directory in split_path:
            if directory == "":
                continue

            if directory == "..":
                current = current.parent
                continue

            if directory == ".":
                continue

            current = current.get_child(directory)

            if current is None:
                return Result(False, message=ResultMessage.FS.PATH_NOT_FOUND)

        return Result(True, data=current)

    def _internal_find(self, path: str):
        """
        Find the inode at the given path. THis is the internal version of find, which does not
        remove the mapped path from the beginning of the path.
        """
        split_path = path.split("/")

        if split_path[0] == "":
            split_path = split_path[1:]

        current = self._root
        for directory in split_path:
            if directory == "":
                continue

            if directory == "..":
                current = current.parent
                continue

            if directory == ".":
                continue

            current = current.get_child(directory)

            if current is None:
                return None

        return current

    def create(self, path: str, owner: int, group_owner: int, mode: int, is_dir: bool):
        # TODO: Implement this better
        parent_path = "/".join(path.split("/")[:-1])
        parent = self._internal_find(parent_path)

        if parent is None:
            # TODO: Return a Result object
            return False

        if is_dir:
            parent.add_child(Directory(path.split("/")[-1], owner, group_owner, mode))
        else:
            parent.add_child(File(path.split("/")[-1], owner, group_owner, mode))

        return True

    def write(self, path: str, data: Union[bytes, str]):
        # TODO: Implement this better
        inode = self._internal_find(path)

        if inode is None:
            return False

        if not inode.is_file():
            return False

        inode._data = data

        return True

    @staticmethod
    def make_standard_filesystem() -> "Ext4":
        fs = Ext4()

        for dir in ["bin", "etc", "home", "lib", "root", "run", "sbin", "proc", "tmp", "usr", "var"]:
            if dir == "root":
                fs._current_directory.add_child(Directory(dir, 0, 0, 0o750))
            elif dir == "proc":
                fs._current_directory.add_child(Directory(dir, 0, 0, 0o555))
            elif dir == "tmp":
                fs._current_directory.add_child(Directory(dir, 0, 0, 0o777))
            else:
                fs._current_directory.add_child(Directory(dir, 0, 0, 0o755))

        ext4_setup.setup_bin(fs)
        ext4_setup.setup_etc(fs)
        ext4_setup.setup_home(fs)
        ext4_setup.setup_lib(fs)
        ext4_setup.setup_proc(fs)
        ext4_setup.setup_root(fs)
        ext4_setup.setup_run(fs)
        ext4_setup.setup_sbin(fs)
        ext4_setup.setup_tmp(fs)
        ext4_setup.setup_usr(fs)
        ext4_setup.setup_var(fs)

        return fs

    def __str__(self):
        return f"Ext4({self._root})"

    def __repr__(self):
        return self.__str__()
