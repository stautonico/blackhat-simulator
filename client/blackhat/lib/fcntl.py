from typing import Optional

from ..helpers import Result
from ..fs import copy as copy_internal

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


def creat(pathname: str, mode: int = 0o644) -> Result:
    """
    Make a file

    Args:
        pathname (str): The path of the file to make
        mode (int): Octal permissions of the new `File`

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_creat(pathname, mode)

def copy(src_path: str, dst_path: str) -> Result:
    """
    A helper function to copy a file/directory from a given `src_path` to the given `dst_path`

    Args:
        src_path (str): The path of the `File`/`Directory` to copy
        dst_path (str): The path to copy to. If the final item in the path doesn't exist, but the item one step up does,
        the final item will be the new name of the `File`/`Directory`

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    # TODO: Find somewhere not stupid to put this
    return copy_internal(computer, src_path, dst_path)