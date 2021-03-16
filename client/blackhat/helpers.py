from enum import Enum
from typing import Union


class SysCallMessages(Enum):
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
    """Something went wrong with the service or the connection on another machine. Similar to error 500 (generic server error)"""


class SysCallStatus:
    """
    Class that contains status information about a "syscall"

    Args:
        success (bool): Success status of the "syscall"
        message (SysCallMessages, optional): Message regarding the status (successful or otherwise). May or may not be used. Changes on a case by case basis
        data (str, optional): Data returned by the function. Changes on a case by case basis

    """

    def __init__(self, success: bool, message: Union[SysCallMessages, None] = None, data=None):
        self.success = success
        self.message = message
        self.data = data

    def __str__(self):
        return f"SysCallStatus(success={self.success}, message={self.message}, data={self.data})"
