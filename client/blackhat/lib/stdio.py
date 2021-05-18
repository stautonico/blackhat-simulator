from typing import Optional

from ..helpers import Result

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


def rename(oldpath: str, newpath: str) -> Result:
    """
    Rename or move a file or directory

    Args:
        oldpath (str): The original file/directory path to rename
        newpath (str): The new path of the file/directory

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    return computer.sys_rename(oldpath, newpath)

