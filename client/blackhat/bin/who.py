from ..computer import Computer
from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "who"
__DESCRIPTION__ = "show who is logged on"
__DESCRIPTION_LONG__ = "Print information about users who are currently logged in."
__VERSION__ = "1.2"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("-b", "--boot", action="store_true", help="time of last system boot")
    parser.add_argument("-H", "--heading", action="store_true", help="print line of column headings")
    parser.add_argument("-q", "--count", action="store_true", help="all login names and number of users logged on")
    parser.add_argument("--version", action="store_true", help=f"print program version")

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
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if args.boot:
            return output(f"\tsystem boot  {computer.boot_time.strftime('%Y-%m-%d %H:%M')}", pipe)

        if args.count:
            usernames = []
            for session in computer.sessions:
                username_result = computer.get_user(session.real_uid)
                if username_result.success:
                    username = username_result.data.username
                else:
                    username = "?"
                if username not in usernames:
                    usernames.append(username)

            return output(f"{' '.join(usernames)}\n# users={len(usernames)}", pipe)

        output_text = ""

        if args.heading:
            output_text += "NAME\tLINE\n"

        for session in computer.sessions:
            username_result = computer.get_user(session.real_uid)
            if username_result.success:
                username = username_result.data.username
            else:
                username = "?"
            output_text += f"{username}\tpts/{session.id}\n"

        return output(output_text, pipe)
