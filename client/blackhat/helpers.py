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
    GENERIC_NETWORK = 12
    """Something went wrong with the service or the connection on another machine. Similar to error http 500"""
    INVALID_ARGUMENT = 13
    """The argument given to the command was invalid for one reason or another"""


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
    F_OK = 1 << 0  # Check for existence
    R_OK = 1 << 1  # Check read bit
    W_OK = 1 << 2  # Check write bit
    X_OK = 1 << 3  # Check execute bit


class timeval:
    def __init__(self, tv_sec, tv_usec):
        self.tv_sec = tv_sec
        self.tv_usec = tv_usec


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
