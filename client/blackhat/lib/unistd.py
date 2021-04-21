from typing import Optional

from ..fs import FSBaseObject
from ..helpers import SysCallStatus, SysCallMessages

computer: Optional["Computer"] = None


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
