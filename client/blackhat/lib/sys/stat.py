from typing import Optional

from ...fs import Directory
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


def mkdir(pathame: str, mode=0o755) -> SysCallStatus:
    # Make sure it doesn't already exist
    find_dir = computer.fs.find(pathame)

    if find_dir.success:
        return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

    # Make sure we have write permissions on the parent dir
    parent_path = "/".join(pathame.split("/")[:-1])

    # Just in case
    find_parent = computer.fs.find(parent_path)

    if not find_parent.success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    if not find_parent.data.check_perm("write", computer).success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_WRITE)

    new_dir = Directory(pathame.split("/")[-1], find_parent.data, owner=computer.get_uid(),
                        group_owner=computer.get_gid())
    if not chmod(pathame, mode).success:
        # rwxr-xr-x
        new_dir.permissions = {"read": ["owner", "group", "public"], "write": ["owner"],
                               "execute": ["owner", "group", "public"]}
    add_file = find_parent.data.add_file(new_dir)

    if not add_file.success:
        return SysCallStatus(success=False, message=SysCallMessages.GENERIC)

    return SysCallStatus(success=True, data=new_dir)


def chmod(pathname: str, mode: int) -> SysCallStatus:
    try:
        find_file = computer.fs.find(pathname)

        if not find_file.success:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        # Only the owner can change chmod permissions
        if computer.get_uid() not in [find_file.data.owner, 0]:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED)

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
        return SysCallStatus(success=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return SysCallStatus(success=False)
