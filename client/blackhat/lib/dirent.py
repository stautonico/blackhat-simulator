from typing import Optional

from ..helpers import Result, ResultMessages

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


def readdir(pathname: str) -> Result:
    """
    Returns a list of items in a given directory

    Args:
        pathname (str): The path of the directory to list

    Returns:
        Result: A result with the data flag containing a list of `FSBaseObject`s
    """
    find_dir: Result = computer.fs.find(pathname)

    if not find_dir.success:
        return Result(success=False, message=ResultMessages.NOT_FOUND)

    if find_dir.data.is_file():
        return Result(success=False, message=ResultMessages.IS_FILE)

    # We need execute permissions to list a directory (???)
    if not find_dir.data.check_perm("execute", computer).success:
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    return Result(success=True, data=[x for x in find_dir.data.files.values()])
