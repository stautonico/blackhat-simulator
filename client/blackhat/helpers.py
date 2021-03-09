from enum import Enum
from typing import Union


class SysCallMessages(Enum):
    """
    Enum: Messages regarding the status of a syscall
    """
    NOT_ALLOWED = 1
    """Call failed due to permission related error"""


class SysCallStatus:
    """
    Class that contains status information about a syscall

    Args:
        success (bool): Success status of the syscall
        message (SysCallMessages, optional): Message regarding the status (successful or otherwise). May or may not be used. Changes on a case by case basis
        data (str, optional): Data returned by the function. Changes on a case by case basis

    """

    def __init__(self, success: bool, message: Union[SysCallMessages, None] = None, data: str = None):
        self.success = success
        self.message = message
        self.data = data
