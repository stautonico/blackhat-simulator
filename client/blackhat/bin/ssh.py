from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output
from ..session import Session

__COMMAND__ = "ssh"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    result = computer.parent.find_client(args[0])

    computer.shell.computers.append(result.data)

    result.data.sessions.append(Session(0, result.data.fs.files, 0))

    return output(result, pipe)
