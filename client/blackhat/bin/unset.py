from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "unset"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: not enough arguments", pipe, success=False)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    for arg in args:
        if arg.startswith("$"):
            arg = arg[1:]
        if arg in computer.sessions[-1].env.keys():
            del computer.sessions[-1].env[arg]

    return output("", pipe)
