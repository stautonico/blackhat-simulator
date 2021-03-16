from ..lib.output import output
from ..helpers import SysCallStatus, SysCallMessages
from ..computer import Computer

__COMMAND__ = "ifconfig"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    return output(computer.lan, pipe)