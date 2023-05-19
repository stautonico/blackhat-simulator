from typing import Optional, Union, Literal, TypeVar, Callable


class Permissions:
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"

    def __init__(self, mode: Union[int, str]):
        self.user = {"read": False, "write": False, "execute": False}
        self.group = {"read": False, "write": False, "execute": False}
        self.other = {"read": False, "write": False, "execute": False}

        if isinstance(mode, int):
            self._from_int(mode)
        elif isinstance(mode, str):
            self._from_str(mode)
        else:
            raise TypeError("mode must be an int or str")

    def _from_int(self, mode: int):
        self.user["read"] = bool(mode & 0o400)
        self.user["write"] = bool(mode & 0o200)
        self.user["execute"] = bool(mode & 0o100)

        self.group["read"] = bool(mode & 0o40)
        self.group["write"] = bool(mode & 0o20)
        self.group["execute"] = bool(mode & 0o10)

        self.other["read"] = bool(mode & 0o4)
        self.other["write"] = bool(mode & 0o2)
        self.other["execute"] = bool(mode & 0o1)

    def _from_str(self, mode: str):
        if len(mode) != 9:
            raise ValueError("mode must be 9 characters long")

        self.user["read"] = mode[0] == "r"
        self.user["write"] = mode[1] == "w"
        self.user["execute"] = mode[2] == "x"

        self.group["read"] = mode[3] == "r"
        self.group["write"] = mode[4] == "w"
        self.group["execute"] = mode[5] == "x"

        self.other["read"] = mode[6] == "r"
        self.other["write"] = mode[7] == "w"
        self.other["execute"] = mode[8] == "x"

    def __repr__(self):
        return f"Permissions({self.user}, {self.group}, {self.other})"

    def __str__(self):
        return f"{self.user}{self.group}{self.other}"


EVENT_TYPE = Literal["read", "write", "move", "change_perm", "change_owner", "delete"]

Inode = TypeVar("Inode", bound="InodeBase")

EventCallback = Callable[[Inode], None]


class Filesystem:
    """
    The generic "template" class that all filesystems should implement.
    The filesystems need to implement the following methods:
    - read
    - write
    - move
    - change_perm
    - change_owner
    - delete

    Maybe more?
    """

    def __init__(self):
        self._mapped_path: Optional[str] = None

    def add_mapping(self, path: str):
        """
        Add a mapping to the filesystem. (So the filesystem knows where its mapped to in the overall scheme of things.)
        :param path: The path to map the filesystem to.
        """
        self._mapped_path = path

    def find(self, path: str):
        """
        Find the path in the filesystem.
        :param path: The path to find.
        :return: The path in the filesystem.
        """
        raise NotImplementedError(f"{type(self).__name__} does not implement find")

    def create(self, path: str, owner: int, group_owner: int, mode: int, is_dir: bool):
        raise NotImplementedError(f"{type(self).__name__} does not implement create")

    def read(self, path: str):
        raise NotImplementedError(f"{type(self).__name__} does not implement read")

    def write(self, path: str, data: Union[bytes, str]):
        raise NotImplementedError(f"{type(self).__name__} does not implement write")

    def move(self, path: str, new_path: str):
        raise NotImplementedError(f"{type(self).__name__} does not implement move")

    def change_perm(self, path: str, perm: Permissions):
        raise NotImplementedError(f"{type(self).__name__} does not implement change_perm")

    def change_owner(self, path: str, owner: int, group_owner: int):
        raise NotImplementedError(f"{type(self).__name__} does not implement change_owner")

    def delete(self, path: str):
        raise NotImplementedError(f"{type(self).__name__} does not implement delete")
