from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "man"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    man - an interface to the system reference manuals

    # TODO: Complete this manpage
    """
    parser = ArgParser(prog=__COMMAND__)

    parser.add_argument("command")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"man {__VERSION__} (miscutils)", pipe)

        if not args.command and not args.version:
            return output(f"What manual page do you want?\nFor example try 'man man'", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output(f"", pipe)
    else:
        # Find the manpage from /usr/share/man
        find_man_result = computer.fs.find(f"/usr/share/man/{args.command}")

        if find_man_result.success:
            read_result = find_man_result.data.read(computer)

            if read_result.success:
                return output(read_result.data, pipe)
            else:
                return output(f"{__COMMAND__}: {args.command}: Permission denied", pipe, success=False)
        else:
            return output(f"{__COMMAND__}: No manual entry for {args.command}", pipe, success=False)
