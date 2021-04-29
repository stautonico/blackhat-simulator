from typing import Optional

from ...helpers import Result
from ...helpers import stat_struct as stat_struct_internal

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


stat_struct = stat_struct_internal


def stat(path: str) -> Result:
    return computer.sys_stat(path)


def mkdir(pathname: str, mode=0o755) -> Result:
    return computer.sys_mkdir(pathname, mode)


def chmod(pathname: str, mode: int) -> Result:
    return computer.sys_chmod(pathname, mode)
