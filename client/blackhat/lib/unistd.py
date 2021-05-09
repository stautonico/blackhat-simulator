from typing import Optional, Literal

from ..fs import FSBaseObject
from ..helpers import Result, ResultMessages
from ..session import Session

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


# TODO: Replace the `get_` functions with something related to pwd.h

def add_user(username: str, password: str, uid: Optional[int] = None, plaintext: bool = True) -> Result:
    if computer.sys_getuid() != 0:
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)
    return computer.add_user(username, password, uid, plaintext)


def get_user(uid: Optional[int] = None, username: Optional[str] = None) -> Result:
    return computer.get_user(uid, username)


def get_all_users() -> Result:
    return computer.get_all_users()


def add_group(name: str, gid: Optional[int] = None) -> Result:
    if computer.sys_getuid() != 0:
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)
    return computer.add_group(name, gid)


def get_group(gid: Optional[int] = None, name: Optional[str] = None) -> Result:
    return computer.get_group(gid, name)


def add_user_to_group(uid: int, gid: int,
                      membership_type: Literal["primary", "secondary"] = "secondary") -> Result:
    if computer.sys_getuid() != 0:
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)
    return computer.add_user_to_group(uid, gid, membership_type)


def get_user_primary_group(uid: int) -> Result:
    return computer.get_user_primary_group(uid)


def get_user_groups(uid: int) -> Result:
    return computer.get_user_groups(uid)


# NOTE: Temporary until I get a realistic version working
def get_sessions() -> Result:
    return Result(success=True, data=computer.sessions)


def reboot(mode: int) -> Result:
    return computer.sys_reboot(mode)


def rmdir(pathname: str) -> Result:
    return computer.sys_rmdir(pathname)


def save(file: Optional[str]) -> bool:
    return computer.save(file)


def execv(pathname: str, argv: list) -> Result:
    return computer.sys_execv(pathname, argv)


def execvp(command: str, argv: list) -> Result:
    return computer.sys_execvp(command, argv)


def new_session(uid:int) -> None:
    # TODO: Make this more realistic since I have no clue how it works in real life
    current_session: Session = computer.sessions[-1]
    # Create a new session
    new_session = Session(uid, current_session.current_dir, current_session.id + 1)
    computer.sessions.append(new_session)
    computer.run_current_user_shellrc()
