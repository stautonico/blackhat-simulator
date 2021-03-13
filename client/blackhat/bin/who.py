from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "who"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    output_text = ""

    for session in computer.sessions:
        username_result = computer.lookup_username(session.real_uid)
        if username_result.success:
            username = username_result.data
        else:
            username = "?"
        output_text += f"{username}\tpts/{session.id}\n"

    if output_text.endswith("\n"):
        output_text = output_text[:-1]

    return output(output_text, pipe)