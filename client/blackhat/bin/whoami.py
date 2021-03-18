from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "whoami"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    lookup_result: SysCallStatus = computer.find_user(computer.get_uid())

    if lookup_result.success:
        return output(lookup_result.data.username, pipe)
    else:
        return output(f"{__COMMAND__}: failed to find username for uid {computer.get_uid()}", pipe, success=False,
                      success_message=SysCallMessages.NOT_FOUND)
