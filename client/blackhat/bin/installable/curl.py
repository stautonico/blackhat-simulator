from ...helpers import Result
from ...lib.input import ArgParser
from ...lib.netdb import gethostbyname
from ...lib.output import output
from ...lib.sys import socket
from ...lib.unistd import write

__COMMAND__ = "curl"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.2"


def parse_args(args=[], doc=False):
    """
    Handle parsing of arguments and flags. Generates docs using help from `ArgParser`

    Args:
        args (list): argv passed to the binary
        doc (bool): If the function should generate and return manpage

    Returns:
        Processed args and a copy of the `ArgParser` object if not `doc` else a `string` containing the generated manpage
    """
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("host")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION__}\n\n"

    for item in arg_helps:
        # Its a positional argument
        if len(item.option_strings) == 0:
            # If the argument is optional:
            if item.nargs == "?":
                SYNOPSIS += f"[{item.dest.upper()}] "
            else:
                SYNOPSIS += f"{item.dest.upper()} "
        else:
            # Boolean flag
            if item.nargs == 0:
                if len(item.option_strings) == 1:
                    DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/\t{item.help}\n\n"
                else:
                    DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/\n\t\t{item.help}\n\n"
            elif item.nargs == "+":
                DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/=[{item.dest.upper()}]...\n\t\t{item.help}\n\n"
            else:
                DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/={item.dest.upper()}\n\t\t{item.help}\n\n"

    if doc:
        return f"{NAME}\n\n{SYNOPSIS}\n\n{DESCRIPTION}\n\n"
    else:
        return args, parser


def main(args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    args, parser = parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    if args.version:
        return output(f"curl {__VERSION__} (blackhet netutils)", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        if ":" in args.host:
            host, port = args.host.split(":")
        else:
            host = args.host
            port = 80

        # Try to resolve the hostname
        resolve_hostname = gethostbyname(host)
        if not resolve_hostname.success:
            return output(f"{__COMMAND__}: (6) Could not resolve host: {host}", pipe, success=False)

        sock = socket.Socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_addr = socket.SockAddr(socket.AF_INET, port, resolve_hostname.data.h_addr)
        connection_result = socket.connect(sock, sock_addr)

        if not connection_result.success:
            return output(f"{__COMMAND__}: (7) Failed to connect to {host} port {port}: Connection refused", pipe,
                          success=False)

        write_result = write(sock, {})

        if not write_result.success:
            return output(f"{__COMMAND__}: (7) Failed to connect to {host} port {port}: Connection refused", pipe,
                          success=False)

        if not write_result.data.get("content"):
            return output(f"{__COMMAND__}: (7) Failed to connect to {host} port {port}: Connection refused", pipe,
                          success=False)

        return output(write_result.data.get("content"), pipe)
