from typing import Optional

from ...helpers import Result

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


# TODO: Make this more realistic, just for convenience as of now
def get_ip() -> Result:
    """
    Get the computers current lan IP address

    Returns:
        Result: A `Result` object with the data flag containing the computers lan ip
    """
    return Result(success=True, data=computer.lan)
