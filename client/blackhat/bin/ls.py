from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.sys.stat import stat

__COMMAND__ = "ls"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.0"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("files", nargs="*", default=".")
    parser.add_argument("-a", dest="all", action="store_true")
    parser.add_argument("-l", dest="long", action="store_true")
    parser.add_argument("--no-color", dest="nocolor", action="store_true")
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


def main(args: list, pipe: bool) -> Result:
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

        output_text = ""
        if len(args.files) > 0:

            for file in args.files:

                response = stat(file)

                if response.success:
                    if len(args.files) > 1:
                        if not response.data.st_isfile:
                            output_text += f"{file}: \n"
                    # TODO: Calculate output
                    # output_text += calculate_output(response.data, computer, all=args.all, long=args.long, nocolor=args.nocolor) + "\n\n"
                else:
                    output_text += f"cannot access '{file}': No such file or directory\n\n"

        # No file args were specified (so print the local dir)
        else:
            response = stat(".")

            if response.success:
                # TODO: Calcualte output
                pass
                # output_text = calculate_output(response.data, computer, all=args.all, long=args.long, nocolor=args.nocolor)
            else:
                return output("Error", pipe, success=False, success_message=ResultMessages.NOT_FOUND)

        if not output_text:
            return output("", pipe)
        else:

            return output(output_text, pipe)

