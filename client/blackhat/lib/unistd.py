from enum import IntFlag
from typing import Optional

from ..fs import FSBaseObject
from ..helpers import SysCallStatus, SysCallMessages

computer: Optional["Computer"] = None


# Modes for access()
class AccessMode(IntFlag):
    F_OK = 1 << 0  # Check for existence
    R_OK = 1 << 1  # Check read bit
    W_OK = 1 << 2  # Check write bit
    X_OK = 1 << 3  # Check execute bit


def update(comp: "Computer"):
    global computer
    computer = comp


def getuid() -> int:
    """
    Returns the UID of the `Computer`'s current user
    Returns:
        int: UID of the `Computers`'s current user (from most recent session)
    """
    return computer.sessions[-1].effective_uid


def getgid() -> int:
    """
    Returns the (primary) GID of the `Computer`'s current user
    Returns:
        int: (primary) GID of the `Computers`'s current user (from most recent session)
    """
    current_uid = getuid()
    result = computer.database.execute(
        "SELECT group_gid FROM group_membership WHERE computer_id=? AND user_uid=? AND membership_type=?",
        (computer.id, current_uid, "primary")).fetchone()

    if result:
        return result[0]
    else:
        # NOTE: possible exploit, but maybe we leave it here on purpose?
        # TODO: Write proof of concept exploit to exploit this exploit
        return 0


def getcwd() -> FSBaseObject:
    """
    Get current directory in the file system

    Returns:
        FSBaseObjectSB: The  user's current directory
    """
    if len(computer.sessions) == 0:
        return computer.fs.files
    else:
        return computer.sessions[-1].current_dir


def setuid(uid: int) -> SysCallStatus:
    # TODO: Implement a PROPER setuid
    # The way setuid should work:
    # If the "caller" uid is root, change the uid to whatever is given
    # If the "caller" isn't root, BUT the setuid bit (not implement yet) is set, the UID can be set to the owner of the file
    # If the "caller" isn't root, and the setuid bit ISN'T set, deny all changes

    if computer.get_uid() == 0:
        computer.sessions[-1].effective_uid = uid
        return SysCallStatus(success=True)
    else:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED)


def gethostname() -> str:
    return "localhost" if not computer.hostname else computer.hostname


def sethostname(hostname: str) -> SysCallStatus:
    # Only root can change the system hostname
    if computer.get_uid() == 0:
        computer.hostname = hostname
        return SysCallStatus(success=True)

    return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED)


def read(filepath: str) -> SysCallStatus:
    # Try to find the file
    find_file = computer.fs.find(filepath)

    if not find_file.success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    if find_file.data.is_directory():
        return SysCallStatus(success=False, message=SysCallMessages.IS_DIRECTORY)

    try_read_file = find_file.data.read(computer)

    if not try_read_file.success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_READ)

    return SysCallStatus(success=True, data=try_read_file.data)


def write(filepath: str, data: str) -> SysCallStatus:
    # Try to find the file
    find_file = computer.fs.find(filepath)

    if not find_file.success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    if find_file.data.is_directory():
        return SysCallStatus(success=False, message=SysCallMessages.IS_DIRECTORY)

    try_write_file = find_file.data.write(data, computer)

    if not try_write_file.success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_WRITE)

    return SysCallStatus(success=True)


def access(pathname: str, mode: int) -> SysCallStatus:
    # We need to find the file no matter what we do, so lets just find it now
    find_file = computer.fs.find(pathname)

    success = True

    if not find_file.success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    file = find_file.data

    if AccessMode.R_OK in mode:
        if not file.check_perm("read", computer).success:
            success = False

    if AccessMode.W_OK in mode:
        if not file.check_perm("write", computer).success:
            success = False

    if AccessMode.X_OK in mode:
        if not file.check_perm("execute", computer).success:
            success = False

    return SysCallStatus(success=success)


def chown(pathname: str, owner: int, group: int) -> SysCallStatus:
    find_file = computer.fs.find(pathname)

    if not find_file.success:
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    file = find_file.data

    change_perms = file.change_owner(computer, owner, group)

    if not change_perms.success:
        return SysCallStatus(success=False, message=change_perms.message)

    return SysCallStatus(success=True)

def chdir(pathname: str) -> SysCallStatus:
    find_file = computer.fs.find(pathname)

    if not find_file.success:
        return SysCallStatus(success=False)

    # We need executable permissions to cd (???)
    check_perm = find_file.data.check_perm("execute", computer)
    if not check_perm.success or getuid() != 0:
        return SysCallStatus(success=False)

    computer.sessions[-1].current_dir = find_file.data
    return SysCallStatus(success=True)