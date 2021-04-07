from ...computer import Computer
from ...helpers import SysCallStatus, SysCallMessages
from ...lib.input import ArgParser
from ...lib.output import output

__COMMAND__ = "curl"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("host")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    if args.version:
        return output(f"curl {__VERSION__} (blackhet netutils)", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        result = computer.send_tcp(args.host, 80, {})

        if not result.success:
            if result.message == SysCallMessages.NOT_FOUND:
                return output(f"{__COMMAND__}: (6) Could not resolve host: {args.host}", pipe, success=False)
            else:
                return output(f"{__COMMAND__}: (7) Failed to connect to {args.host} port 80: Connection refused", pipe,
                              success=False)
        else:
            return output(result, pipe)
