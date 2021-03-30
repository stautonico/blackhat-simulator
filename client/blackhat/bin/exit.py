from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "exit"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)
    # -f is force (immediately exit)
    if "-f" in args:
        if len(computer.shell.computers) == 1:
            computer.save()
            exit(0)
        else:
            computer.sessions = []
            computer.shell.computers.pop()

    if len(computer.shell.computers) == 1:
        if len(computer.sessions) == 1:
            computer.save()
            exit(0)
        else:
            computer.sessions.pop()
    else:
        computer.shell.computers.pop()

    return output("", pipe)
