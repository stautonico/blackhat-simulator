from ..lib.output import output
from ..helpers import SysCallStatus, SysCallMessages
from ..computer import Computer

__COMMAND__ = "man"
__VERSION__ = "1.0.0"
__DOC__ = "man - an interface to the system reference manuals"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output(f"What manual page do you want?\nFor example try 'man man'", pipe)

    # Find the manpage from /usr/share/man
    command = args[0]
    find_man_result = computer.fs.find(f"/usr/share/man/{command}")

    if find_man_result.success:
        read_result = find_man_result.data.read(computer.get_uid(), computer)

        if read_result.success:
            return output(read_result.data, pipe)
        else:
            return output(f"{__COMMAND__}: {command}: Permission denied", pipe, success=False)
    else:
        return output(f"{__COMMAND__}: No manual entry for {command}", pipe, success=False)