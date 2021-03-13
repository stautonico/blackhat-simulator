from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "printenv"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    output_text = ""

    for key, value in computer.sessions[-1].env.items():
        output_text += f"{key}={value}\n"

    if output_text.endswith("\n"):
        output_text = output_text[:-1]

    return output(output_text, pipe)
