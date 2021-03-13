from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "cd"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        computer.sessions[-1].current_dir = computer.fs.files
        return output("", pipe)

    response = computer.fs.find(args[0])

    if response.success:
        if response.data.is_file():
            return output(f"{__COMMAND__}: not a directory: {args[0]}", pipe, success=False,
                          success_message=SysCallMessages.IS_FILE)
        else:
            computer.sessions[-1].current_dir = response.data
            return output("", pipe)
    else:
        return output(f"{__COMMAND__}: no such file or directory: {args[0]}", pipe, success=False,
                      success_message=SysCallMessages.NOT_FOUND)
