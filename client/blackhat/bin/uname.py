from ..lib.output import output
from ..helpers import SysCallStatus, SysCallMessages
from ..computer import Computer

__COMMAND__ = "uname"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (h3xNet coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output("Linux", pipe)

    if "-a" in args:
        return output(f"Linux {computer.hostname} 1.0.0 i686 x86_64 Blackhat/Linux", pipe)

    output_text = ""

    if "-s" in args:
        output_text += "Linux "

    if "-n" in args:
        output_text += f"{computer.hostname} "

    if "-r" in args:
        output_text += "1.0.0 "

    if "-m" in args:
        output_text += "i686 "

    if "-p" in args:
        output_text += "x68_64 "

    if "-o" in args:
        output_text += "Blackhat/Linux"

    return output(output_text, pipe)
