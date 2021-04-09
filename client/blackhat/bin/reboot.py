from time import sleep

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "reboot"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    if args.version:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # Only root can reboot
        if computer.get_uid() == 0:
            print(f"Rebooting...")
            sleep(1)
            computer.run_command("clear", [], pipe=True)
            computer.init()
            while len(computer.sessions) != 1:
                computer.run_command("exit", [], pipe=True)

            return output("", pipe)
        else:
            return output(f"{__COMMAND__}: permission denied", pipe, success=False)
