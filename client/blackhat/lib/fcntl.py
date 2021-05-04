from typing import Optional

from ..helpers import Result
from ..fs import copy as copy_internal

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


def creat(pathname: str, mode: int = 0o644) -> Result:
    return computer.sys_creat(pathname, mode)

def copy(src_path: str, dst_path: str) -> Result:
    # TODO: Find somewhere not stupid to put this
    return copy_internal(computer, src_path, dst_path)