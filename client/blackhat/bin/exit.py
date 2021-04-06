from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "exit"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if args.version:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        if args.force:
            if len(computer.shell.computers) == 1:
                computer.save()
                exit(0)
            else:
                computer.sessions = []
                computer.shell.computers.pop()

        if len(computer.shell.computers) == 1:
            if len(computer.sessions) == 1:
                computer.save()
                exit(0)
            else:
                computer.sessions.pop()
        else:
            computer.shell.computers.pop()

    return output("", pipe)
