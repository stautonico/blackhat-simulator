from enum import Enum
from enum import IntFlag
from typing import Union

class ResultMessages(Enum):
    """
    Enum: Messages regarding the status of a syscall
    """
    NOT_ALLOWED = 1
    """Call failed due to permission related error"""
    ALREADY_EXISTS = 2
    """Object attempting to be created already exists (ex. `User` with given username already exists)"""
    NOT_FOUND = 3
    """The given object doesn't exist"""
    GENERIC = 4
    """Some unknown error occurred"""
    IS_FILE = 5
    """Error when a directory was expected but a file was given instead"""
    IS_DIRECTORY = 6
    """Error when a file was expected but a directory was given instead"""
    MISSING_ARGUMENT = 7
    """Used for binaries"""
    TOO_MANY_ARGUMENTS = 8
    """Used for binaries"""
    NOT_ALLOWED_READ = 9
    """Same as generic `NOT_ALLOWED` but more specific"""
    NOT_ALLOWED_WRITE = 10
    """Same as generic `NOT_ALLOWED` but more specific"""
    EMPTY = 11
    """We're trying to use a space that is completely full"""
    NOT_EMPTY = 12
    """We're trying to remove a directory thats not empty"""
    GENERIC_NETWORK = 13
    """Something went wrong with the service or the connection on another machine. Similar to error http 500"""
    INVALID_ARGUMENT = 14
    """The argument given to the command was invalid for one reason or another"""
    NOT_CONNECTED = 15
    """The socket we're trying to write to isn't connected to anything"""


class Result:
    """
    Class that contains status information about a "syscall"

    Args:
        success (bool): Success status of the "syscall"
        message (ResultMessages, optional): Message regarding the status (successful or otherwise). May or may not be used. Changes on a case by case basis
        data (str, optional): Data returned by the function. Changes on a case by case basis

    """

    def __init__(self, success: bool, message: Union[ResultMessages, None] = None, data=None):
        self.success = success
        self.message = message
        self.data = data

    def __str__(self):
        return f"Result(success={self.success}, message={self.message}, data={self.data})"

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Result):
            return self.success == other.success and self.message == other.message and self.data == other.data
        return False


# Modes for access()
class AccessMode(IntFlag):
    """
    Argument for the `sys_access` system call
    """
    F_OK = 1 << 0  # Check for existence
    R_OK = 1 << 1  # Check read bit
    W_OK = 1 << 2  # Check write bit
    X_OK = 1 << 3  # Check execute bit


class RebootMode(IntFlag):
    """
    Argument for the `sys_reboot` system call
    """
    LINUX_REBOOT_CMD_POWER_OFF = 1 << 0  # Shut down the computer
    LINUX_REBOOT_CMD_RESTART = 1 << 1    # Reboot the computer

class timeval:
    """
    Struct for time related functions
    """
    def __init__(self, tv_sec, tv_usec):
        self.tv_sec = tv_sec
        self.tv_usec = tv_usec


class stat_struct:
    """
    Result of a stat()
    """
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

    def __str__(self):
        output = "{\n"
        output += f"    st_isfile: {self.st_isfile}\n"
        output += f"    st_mode: {self.st_mode}\n"
        output += f"    st_nlink: {self.st_nlink}\n"
        output += f"    st_uid: {self.st_uid}\n"
        output += f"    st_gid: {self.st_gid}\n"
        output += f"    st_size: {self.st_size}\n"
        output += f"    st_atime: {self.st_atime}\n"
        output += f"    st_mtime: {self.st_mtime}\n"
        output += f"    st_ctime: {self.st_ctime}\n"
        output += f"    st_path: {self.st_path}\n"
        output += "}"
        return output


class passwd:
    """
    An entry in the systems users database
    """
    def __init__(self, username: str, password: str, uid: int, gid: int, gecos: str = None, home_dir: str = None):
        self.pw_name = username
        self.pw_passwd = password
        self.pw_uid = uid
        self.pw_gid = gid
        self.pw_gecos = gecos
        self.pw_dir = home_dir if home_dir else f"/home/{self.pw_name}"

    def __str__(self):
        output = "{\n"
        output += f"    pw_name: {self.pw_name}\n"
        output += f"    pw_passwd: {self.pw_passwd}\n"
        output += f"    pw_uid: {self.pw_uid}\n"
        output += f"    pw_gid: {self.pw_gid}\n"
        output += f"    pw_gecos: {self.pw_gecos}\n"
        output += f"    pw_dir: {self.pw_dir}\n"
        output += "}"
        return output



