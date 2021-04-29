from ..computer import Computer
from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "man"
__DESCRIPTION__ = "an interface to the system reference manuals"
__DESCRIPTION_LONG__ = "man is the system's manual pager.  Each page argument given to man is normally the name of a program, utility or function."
__VERSION__ = "1.2"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("command")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION_LONG__}\n\n"

    for item in arg_helps:
        # Its a positional argument
        if len(item.option_strings) == 0:
            # If the argument is optional:
            if item.nargs == "?":
                SYNOPSIS += f"[{item.dest.upper()}] "
            elif item.nargs == "+":
                SYNOPSIS += f"[{item.dest.upper()}]... "
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


def main(computer: Computer, args: list, pipe: bool) -> Result:
    args, parser = parse_args(args)

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
