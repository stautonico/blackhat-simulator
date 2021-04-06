from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "pwd"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: too many arguments", pipe, success=False)

    if args.version:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        return output(computer.get_pwd().pwd(), pipe)
