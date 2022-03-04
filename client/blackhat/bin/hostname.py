__package__ = "blackhat.bin"

from ..helpers import Result
from ..lib.arpa.inet import get_ip
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.sys.stat import stat
from ..lib.unistd import getuid, gethostname, sethostname, read

__COMMAND__ = "hostname"
__DESCRIPTION__ = "show or set system hostname"
__VERSION__ = "1.2"


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
    parser.add_argument("name", nargs="?")
    parser.add_argument("-f", "--fqdn", "--long", action="store_true", help="DNS host name or FQDN")
    parser.add_argument("-F", "--file", help="set host name or NIS domain from FILE", dest="file")
    parser.add_argument("-i", "--ip-addresses", dest="ip_addresses", action="store_true",
                        help="addresses for the host name")
    parser.add_argument("-s", "--short", action="store_true", help="short host name")
    parser.add_argument("-?", action="help", help="shows this help message and exit")
    parser.add_argument("--usage", action="help", help="shows this help message and exit")
    parser.add_argument("-V", "--version", action="store_true", help=f"print program version")

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
    # TODO: Add hostname aliases
    # TODO: Add local domain names (NIS/YP)

    args, parser = parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # Change hostname by file
        if args.file:
            # Only root can change the system hostname
            if getuid() != 0:
                return output(f"{__COMMAND__}: you must be root to change the host name", pipe, success=False)

            find_file = stat(args.file)

            if not find_file.success:
                return output(f"{__COMMAND__}: No such file or directory", pipe, success=False)

            if not find_file.data.st_isfile:
                return output(f"{__COMMAND__}: the specified hostname is invalid", pipe, success=False)

            read_result = read(args.file)

            if not read_result.success:
                return output(f"{__COMMAND__}: Failed to read file", pipe, success=False)

            result = sethostname(read_result.data)
            if not result.success:
                return output(f"{__COMMAND__}: Failed to update system hostname", pipe, success=False)

        if args.fqdn:
            # TODO: Recognize FDQNs
            return output(gethostname(), pipe)

        if args.ip_addresses:
            # TODO: Make this more realistic, just for convenience as of now
            return output(get_ip().data if get_ip().data else "", pipe)

        if args.short:
            # TODO: Shorten FQDN
            return output(gethostname(), pipe)

        if args.name:
            # Only root can change the system hostname
            if getuid() != 0:
                return output(f"{__COMMAND__}: you must be root to change the host name", pipe, success=False)

            result = sethostname(args.name)
            if not result.success:
                return output(f"{__COMMAND__}: Failed to update system hostname", pipe, success=False)

        return output(gethostname(), pipe)
