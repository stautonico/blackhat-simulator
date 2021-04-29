from typing import Optional

from ..fs import FSBaseObject
from ..helpers import Result

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
    return computer.sys_getuid()


def getgid() -> int:
    """
    Returns the (primary) GID of the `Computer`'s current user
    Returns:
        int: (primary) GID of the `Computers`'s current user (from most recent session)
    """
    return computer.sys_getgid()


def getcwd() -> FSBaseObject:
    """
    Get current directory in the file system

    Returns:
        FSBaseObjectSB: The  user's current directory
    """
    return computer.sys_getcwd()


def setuid(uid: int) -> Result:
    return computer.sys_setuid(uid)


def gethostname() -> str:
    return computer.sys_gethostname()


def sethostname(hostname: str) -> Result:
    return computer.sys_sethostname(hostname)


def read(filepath: str) -> Result:
    return computer.sys_read(filepath)


def write(filepath: str, data: str) -> Result:
    return computer.sys_write(filepath, data)


def access(pathname: str, mode: int) -> Result:
    return computer.sys_access(pathname, mode)


def chown(pathname: str, owner: int, group: int) -> Result:
    return computer.sys_chown(pathname, owner, group)


def chdir(pathname: str) -> Result:
    return computer.sys_chdir(pathname)
