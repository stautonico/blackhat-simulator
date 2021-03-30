from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.output import output

__COMMAND__ = "curl"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: More arguments are required", pipe, success=False)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    result = computer.send_tcp(args[0], 22, {"name": "steve"})

    if not result.success:
        if result.message == SysCallMessages.NOT_FOUND:
            return output(f"{__COMMAND__}: (6) Could not resolve host: {args[0]}", pipe, success=False)
        else:
            return output(f"{__COMMAND__}: (7) Failed to connect to {args[0]} port 80: Connection refused", pipe,
                          success=False)
    else:
        return output(result, pipe)
