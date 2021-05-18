from typing import Optional

from ...helpers import Result
from ...helpers import timeval as timevalinternal

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


# This is here so we can `from sys.time import timeval`
# And also so we dont have to have two declarations of the same thing
timeval = timevalinternal


def gettimeofday() -> Result:
    """
    Get the current time (host systems time)

    Returns:
        timeval: A `timeval` struct containing the current time in seconds
    """
    return computer.sys_gettimeofday()
