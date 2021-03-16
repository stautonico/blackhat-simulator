from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "users"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    Slightly different from the standard linux command with the same name
    This command displays all users that exist in the system

    Args:
        computer:
        args:
        pipe:

    Returns:

    """
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    output_text = ""
    for user in computer.users.values():
        output_text += f"{user.username} "

    return output(output_text, pipe)
