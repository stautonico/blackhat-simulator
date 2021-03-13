from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "exit"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # -f is force (immediately exit)
    if "-f" in args:
        exit(0)

    # We don't have any previous sessions to exit to
    if len(computer.sessions) == 1:
        exit(0)
    else:
        computer.sessions.pop()
        return output("", pipe)