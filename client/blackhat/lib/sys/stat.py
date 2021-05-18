from typing import Optional

from ...helpers import Result
from ...helpers import stat_struct as stat_struct_internal

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


stat_struct = stat_struct_internal


def stat(path: str) -> Result:
    """
    Get information about a given file

    Args:
        path (str): The path of the given `File`/`Directory` to get info about

    Returns:
        Result: A `Result` object with the success flag set accordingly and the data flag containing a `stat_struct` object if successful
    """
    return computer.sys_stat(path)


def mkdir(pathname: str, mode=0o755) -> Result:
    """
    Make a directory

    Args:
        pathname (str): The path of the directory to make
        mode (int): Octal permissions of the new `Directory`

    Returns:
        Result: A `Result` object with the success flag set accordingly and the data flag containing the new `Directory` object if successful
    """
    return computer.sys_mkdir(pathname, mode)


def chmod(pathname: str, mode: int) -> Result:
    """
    Change the permission mode of a `File`/`Directory`

    Args:
        pathname (str): File path of the `File`/`Directory` to change mode of
        mode (int): Octal permissions of the given pathname

    Returns:
        Result: A `Result` instance with the `success` flag set accordingly.
    """
    return computer.sys_chmod(pathname, mode)
