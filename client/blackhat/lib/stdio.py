from typing import Optional

from ..helpers import Result

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


def rename(oldpath: str, newpath: str) -> Result:
    return computer.sys_rename(oldpath, newpath)

