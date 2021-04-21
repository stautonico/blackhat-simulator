from typing import Optional

from ...helpers import SysCallStatus, SysCallMessages

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


class stat_struct:
    def __init__(self, st_isfile: bool, st_mode: int, st_nlink: int, st_uid: int, st_gid: int, st_size: float,
                 st_atime: int, st_mtime: int, st_ctime: int, st_path: str):
        self.st_isfile: bool = st_isfile  # Bool telling if file or is dir
        self.st_mode: int = st_mode  # chmod mode
        self.st_nlink: int = st_nlink  # How many links
        self.st_uid: int = st_uid  # UID of owner
        self.st_gid: int = st_gid  # GID of owner
        self.st_size: float = st_size  # Size in bytes
        self.st_atime: int = st_atime  # Last access time (unix time stamp)
        self.st_mtime: int = st_mtime  # Last modified time (unix time stamp)
        self.st_ctime: int = st_ctime  # Last file status change time (unix time stamp)
        self.st_path: str = st_path  # Path in the filesystem
        # Access: Read
        # Modified: Write (content)
        # Change: Change metadata (perms)


def stat(path: str) -> SysCallStatus:
    find_file = computer.fs.find(path)

    if not find_file.success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

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

    return SysCallStatus(success=True, data=stat_result)
