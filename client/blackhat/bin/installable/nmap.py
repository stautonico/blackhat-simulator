__package__ = "blackhat.bin.installable"

from tabulate import tabulate

from ...helpers import Result
from ...lib.input import ArgParser
from ...lib.netdb import gethostbyname
from ...lib.output import output

__COMMAND__ = "nmap"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.2"

from ...lib.sys import socket


def parse_args(args=None, doc=False):
    """
    Handle parsing of arguments and flags. Generates docs using help from `ArgParser`

    Args:
        args (list): argv passed to the binary
        doc (bool): If the function should generate and return manpage

    Returns:
        Processed args and a copy of the `ArgParser` object if not `doc` else a `string` containing the generated manpage
    """
    if args is None:
        args = []
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("host")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if not doc:
        return args, parser

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION__}\n\n"

    for item in arg_helps:
        # it's a positional argument
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

    return f"{NAME}\n\n{SYNOPSIS}\n\n{DESCRIPTION}\n\n"

def main(args: list, pipe: bool) -> Result:
    """
    nmap - Network exploration tool and security / port scanner

    # TODO: Complete this manpage
    """
    # TODO: Add some of the flags that nmap has

    args, parser = parse_args(args)

    if parser.error_message:
        # `host` argument is required unless we have --version
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.host and not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    else:
        # If we specific -h/--help, args will be empty, so exit gracefully
        if not args:
            return output(f"", pipe)
        else:
            # Try to resolve the hostname
            resolve_host = gethostbyname(args.host)
            if not resolve_host.success:
                return output(f"{__COMMAND__}: Could not resolve host: {args.host}", pipe, success=False)

            if resolve_host.data.h_addr != args.host:
                domain_name = True
            else:
                domain_name = False

            # Lets try to find the connect by address
            sock = socket.Socket(socket.AF_INET, socket.SOCK_STREAM)
            addr_struct = socket.SockAddr(socket.AF_INET, 0, resolve_host.data.h_addr)
            connect = socket.connect(sock, addr_struct)

            if not connect:
                return output(f"{__COMMAND__}: Failed to connect to {args.host}: Connection timed out", pipe, success=False)

            # Now, lets generate a table for outputting
            # Table format is [[<PORT>/tcp, "open", <SERVICE_NAME>]]
            headers = ["PORT", "STATE", "SERVICE"]
            table = []
            # Loop through each port and try to connect
            for x in range(1, 65535 + 1):
                sock = socket.Socket(socket.AF_INET, socket.SOCK_STREAM)
                addr_struct = socket.SockAddr(socket.AF_INET, x, resolve_host.data.h_addr)
                connect = socket.connect(sock, addr_struct)

                if connect.success:
                    table.append([f"{x}/tcp", "open", f"{sock.metadata.get('name')} {sock.metadata.get('version')}"])

            # Initial message is different depending on if we passed an ip address or domain name
            if domain_name:
                output_text = f"Nmap scan report for {args.host} ({resolve_host.data.h_addr})"
            else:
                output_text = f"Nmap scan report for {args.host}"


            output_text += "\n" + tabulate(table, headers=headers, tablefmt="plain")

            return output(output_text, pipe)
