from typing import Optional

from ...helpers import Result

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


# TODO: Make this more realistic, just for convenience as of now
def get_ip() -> Result:
    return Result(success=True, data=computer.lan)
