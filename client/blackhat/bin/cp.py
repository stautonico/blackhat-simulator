from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.fcntl import copy

__COMMAND__ = "cp"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.1"

def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("-r", dest="recursive", action="store_true")
    parser.add_argument("-p", dest="preserve_permissions", action="store_true")
    parser.add_argument("-v", dest="verbose", action="store_true")
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

def main(args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
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

        result = copy(args.source, args.destination)

        if not result.success:
            if result.message == ResultMessages.NOT_FOUND:
                return output(f"{__COMMAND__}: cannot find '{args.destination}': No such file or directory", pipe,
                              success=False)

            elif result.message == ResultMessages.NOT_ALLOWED:
                return output(f"{__COMMAND__}: cannot open '{args.source}': Permission denied", pipe,
                              success=False)

            elif result.message == ResultMessages.NOT_ALLOWED_READ:
                return output(f"{__COMMAND__}: cannot open '{args.source}' for reading: Permission denied", pipe,
                              success=False)

            elif result.message == ResultMessages.NOT_ALLOWED_WRITE:
                return output(f"{__COMMAND__}: cannot open '{args.source}' for writing: Permission denied", pipe,
                              success=False)

            elif result.message == ResultMessages.ALREADY_EXISTS:
                return output(f"{__COMMAND__}: cannot write '{args.destination}: Directory already exists", pipe,
                              success=False)

        return output("", pipe)
        # # Make sure we have proper permissions before copying
        # if src_result.data.check_perm("read", computer).success and src_result.data.check_perm(
        #         "write", computer).success:
        #     copy_result = copy(computer, src_result.data, args.destination, True, args.verbose)
        #
        #     if not copy_result.success:
        #         if copy_result.message == ResultMessages.NOT_FOUND:
        #             return output(f"{__COMMAND__}: cannot find '{args.destination}': No such file or directory", pipe,
        #                           success=False)
        #         elif copy_result.message == ResultMessages.GENERIC:
        #             return output(f"{__COMMAND__}: invalid destination '{args.destination}'", pipe, success=False)
        #         elif copy_result.message == ResultMessages.NOT_ALLOWED_READ:
        #             return output(f"{__COMMAND__}: cannot open '{args.source}' for reading: Permission denied", pipe,
        #                           success=False)
        #         elif copy_result.message == ResultMessages.NOT_ALLOWED_WRITE:
        #             return output(f"{__COMMAND__}: cannot open '{args.destination} for writing: Permission denied", pipe,
        #                           success=False)
        #         elif copy_result.message == ResultMessages.ALREADY_EXISTS:
        #             return output(f"{__COMMAND__}: cannot write '{args.destination}: Directory already exists", pipe,
        #                           success=False)
        #     else:
        #         computer.run_command("rm", [args.source, "-r"], pipe)
        #         if args.verbose:
        #             print(f"{args.source} -> {args.destination}")
        #         return output("", pipe)
        # else:
        #     return output(f"{__COMMAND__}: cannot open '{args.source}': Permission denied", pipe, success=False)
