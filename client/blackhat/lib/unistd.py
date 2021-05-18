from typing import Optional, Literal, Union

from .sys.socket import Socket
from ..fs import FSBaseObject
from ..helpers import Result, ResultMessages
from ..session import Session

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    """
    Store a reference to the games current `Computer` object as a global variable so methods can reference it without
    requiring it as an argument
    
    Args:
        comp (:obj:`Computer`): The games current `Computer` object

    Returns:
        None
    """
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
    """
    Change current `Session`'s effective UID to the given `UID`

    Notes:
        setuid() followed the current rules:
            * If the "caller" uid is root, change the uid to whatever is given
            * If the "caller" isn't root, BUT the setuid bit (not implement yet) is set, the UID can be set to the owner of the file
            * If the "caller" isn't root, and the setuid bit ISN'T set, deny all changes

    Args:
        uid (int): The new UID to change to

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_setuid(uid)


def gethostname() -> str:
    """
    Gets the current system hostname (from internal var, not /etc/hostname)

    Returns:
        str: "localhost" if the hostname isn't set, otherwise, the current `Computer`'s hostname
    """
    return computer.sys_gethostname()


def sethostname(hostname: str) -> Result:
    """
    An easy function to update the hostname (also updates /etc/hostname)
    Args:
        hostname (str): The `Computer`'s new hostname

    Returns:
        Result: A `Result` instance with the `success` flag set accordingly.
    """
    return computer.sys_sethostname(hostname)


def read(filepath: str) -> Result:
    """
    Try to read the content of the given `filepath`. Checks permissions

    Args:
        filepath (str): The path of the file to read

    Returns:
        Result: A `Result` object with the success flag set accordingly and the data flag containing the files
        if read was successful
    """
    return computer.sys_read(filepath)


def write(fd: Union[str, Socket], data: Union[str, dict]) -> Result:
    """
    Try to write to a given file descriptor. If `fd` is a file path, this function will try to write to a file
    (permission safe), however, if the fd is a `Socket`, this function will try to send the given `data` to the
    respective `Socket`'s connected service (if connected).

    Args:
        fd (str or :obj:`Socket`): The filepath of the file or Socket to write to
        data (str or dict): The data to write to the file (if fd == str) or data to send to the socket (if fd == Socket)

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_write(fd, data)


def access(pathname: str, mode: int) -> Result:
    """
    Check if the current effective UID has a given permission to the given `File`/`Directory`
    Possible modes are:
        * F_OK: File exists
        * R_OK: Read permission
        * W_OK: Write permissions
        * X_OK: Execute permission

    Args:
        pathname (str): The file path of the given `File`/`Directory` to check
        mode (int): Bitwise flags of the permissions to check

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_access(pathname, mode)


def chown(pathname: str, owner: int, group: int) -> Result:
    """
    Change the owner of the given `pathname` (if allowed)

    Notes:
        Only the owner or root is allowed to change the owner of a `File`/`Directory`

    Args:
        pathname (str): The file path of the `File`/`Directory` to change the owner of
        owner (int): The UID of the new owner
        group (int): The GID of the new owner

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_chown(pathname, owner, group)


def chdir(pathname: str) -> Result:
    """
    Change the `current_dir` of the current `Session`

    Args:
        pathname (str): The file path of the directory to `cd` into

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_chdir(pathname)


# TODO: Replace the `get_` functions with something related to pwd.h

def add_user(username: str, password: str, uid: Optional[int] = None, plaintext: bool = True) -> Result:
    """
    Add a new user to the system (permission safe).
    This function also generates the UID for the new user (unless manually specified)

    Args:
        username (str): The username for the new user
        password (str): The plaintext password for the new user
        uid (int, optional): The UID of the new user
                    plaintext (bool): If the given `new_password` is plain text or an MD5 hash

    Returns:
        Result: A `Result` instance with the `success` flag set accordingly. The `data` flag contains the new users UID if successful.
    """
    if computer.sys_getuid() != 0:
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)
    return computer.add_user(username, password, uid, plaintext)


def get_user(uid: Optional[int] = None, username: Optional[str] = None) -> Result:
    """
    Find a user in the database by UID or username
    Args:
        uid (int, optional): The UID of the user to find
        username (str, optional): The username of the user to find

    Returns:
        Result: A `Result` with the `success` flag set accordingly. The `data` flag contains the user dict if found
    """
    return computer.get_user(uid, username)


def get_all_users() -> Result:
    """
    Get all users that exist in the given system in the given format:

    Returns:
        Result: A `Result` with the `data` flag containing the array of `User`s
    """
    return computer.get_all_users()


def add_group(name: str, gid: Optional[int] = None) -> Result:
    """
    Add a new group to the system (permission safe).
    This function also generates the GID for the new group (unless manually specified)

    Args:
        name (str): The name for the new group
        gid (int, optional): The GID of the new user

    Returns:
        Result: A `Result` instance with the `success` flag set accordingly. The `data` flag contains the GID if successful.
    """
    if computer.sys_getuid() != 0:
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)
    return computer.add_group(name, gid)


def get_group(gid: Optional[int] = None, name: Optional[str] = None) -> Result:
    """
    Find a group in the database by GID or name or both
    Args:
        gid (int, optional): The GID of the group to find
        name (str, optional): The name of the group to find

    Returns:
        Result: A `Result` with the `success` flag set accordingly. The `data` flag contains the group dict if found
    """
    return computer.get_group(gid, name)


def add_user_to_group(uid: int, gid: int,
                      membership_type: Literal["primary", "secondary"] = "secondary") -> Result:
    """
    Add a user to a group (by uid and gid) (permission safe)

    Args:
        uid (int): The UID of the user
        gid (int): The GID of the group to add the user to
        membership_type (str): The type of group relationship (primary, secondary)

    Returns:
        Result: A `Result` object with the `success` flag set accordingly
    """
    if computer.sys_getuid() != 0:
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)
    return computer.add_user_to_group(uid, gid, membership_type)


def get_user_primary_group(uid: int) -> Result:
    """
    Get the `Group` GID's that is the `User`s primary `Group` (by UID)

    Args:
        uid (int): The UID of the user to lookup

    Returns:
        Result: A `Result` with the `data` flag containing a list of GIDs
    """
    return computer.get_user_primary_group(uid)


def get_user_groups(uid: int) -> Result:
    """
    Get the list of `Group` GID's that the `User` belongs to (by UID)

    Args:
        uid (int): The UID of the user to lookup

    Returns:
        Result: A `Result` with the `data` flag containing a list of GIDs
    """
    return computer.get_user_groups(uid)


# NOTE: Temporary until I get a realistic version working
def get_sessions() -> Result:
    """
    Get all the current open sessions in the computer

    Returns:
        Result: A `Result` object containing a list of all the `Computer`s open session
    """
    return Result(success=True, data=computer.sessions)


def reboot(mode: int) -> Result:
    """
    Simulate a computer reboot. Clear all sessions and re-initialize the machine

    Args:
        mode (int: Bitwise flags of the operation to take

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_reboot(mode)


def rmdir(pathname: str) -> Result:
    """
    Remove an empty directory

    Args:
        pathname (str): The file path of the empty `Directory` to remove

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_rmdir(pathname)


def save(file: Optional[str]) -> bool:
    """
    Serialize and dump the current `Computer` (and everything that's connected to it (`StandardFS`, `File`s, etc)) to a file
    Args:
        output_file (str, optional): The file to dump the contents to

    Returns:
        bool: `True` if the dump/save was successful, otherwise `False`
    """
    return computer.save(file)


def execv(pathname: str, argv: list) -> Result:
    """
    Execute a file

    Args:
        pathname (str): The path name of the binary to execute
        argv (list): A list of arguments to pass to the binary

    Returns:
        Result: A `Result` arguments containing the output from the binary
    """
    return computer.sys_execv(pathname, argv)


def execvp(command: str, argv: list) -> Result:
    """
    Execute a command using the PATH rather than the full binary path. Does exactly what the system shell does.

    Args:
        command (str): The command to run
        argv (list): A list of arguments to pass to the binary

    Returns:
        Result: A `Result` arguments containing the output from the binary
    """
    return computer.sys_execvp(command, argv)


def new_session(uid: int) -> None:
    """
    Temporary function: Open a new session in the current `Computer`

    Args:
        uid (int): The real UID of the user in the new `Session`

    Returns:
        None
    """
    # TODO: Make this more realistic since I have no clue how it works in real life
    current_session: Session = computer.sessions[-1]
    # Create a new session
    new_session = Session(uid, current_session.current_dir, current_session.id + 1)
    computer.sessions.append(new_session)
    computer.run_current_user_shellrc()


def unlink(pathname: str) -> Result:
    """
    Removes a link to a file. If there are no links left, the file is removed.

    Args:
        pathname (str): The file path of the `File` to unlink

    Returns:
        Result: A `Result` arguments containing the output from the binary

    """
    return computer.sys_unlink(pathname)
