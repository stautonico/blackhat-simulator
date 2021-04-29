from typing import Optional

from ...helpers import Result
from ...helpers import timeval as timevalinternal

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


# This is here so we can `from sys.time import timeval`
# And also so we dont have to have two declarations of the same thing
timeval = timevalinternal


def gettimeofday() -> Result:
    return computer.sys_gettimeofday()
