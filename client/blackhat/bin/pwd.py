from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "pwd"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output(computer.get_pwd().pwd(), pipe)
    else:
        return output(f"{__COMMAND__}: too many arguments", pipe, success=False, success_message=SysCallMessages.TOO_MANY_ARGUMENTS)