from time import time
from typing import Optional

from ...helpers import SysCallStatus

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


class timeval:
    def __init__(self, tv_sec, tv_usec):
        self.tv_sec = tv_sec
        self.tv_usec = tv_usec


def gettimeofday() -> SysCallStatus:
    # TODO: Add get time by timezone
    timestamp = time()
    seconds = int(timestamp)
    microseconds = int(str(timestamp - seconds).replace("0.", ""))

    return SysCallStatus(success=True, data=timeval(seconds, microseconds))
