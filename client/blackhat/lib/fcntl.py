from typing import Optional

from ..helpers import Result

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


def creat(pathname: str, mode: int = 0o644) -> Result:
    return computer.sys_creat(pathname, mode)
