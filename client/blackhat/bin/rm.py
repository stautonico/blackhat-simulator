__package__ = "blackhat.bin"

from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import getcwd, unlink
from ..lib.sys.stat import stat
from ..lib.dirent import readdir

__COMMAND__ = "rm"
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
    parser.add_argument("source")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-r", "-R", "--recursive", action="store_true")
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
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # Special case for * (all files in current dir)
        to_delete = []

        if args.source == "*":
            for file in getcwd().files:
                to_delete.append(file)
        elif "*" in args.source:
            if args.source[-1] != "*":
                return output(f"{__COMMAND__}: cannot find '{args.source}': No such file or directory", pipe,
                              success=False)
            else:
                # Find the dir without the star
                path_without_star = "/".join(args.source.split("/")[:-1])
                result = readdir(path_without_star)
                if not result.success:
                    return output(f"{__COMMAND__}: cannot find '{args.source}': No such file or directory", pipe,
                                  success=False)
                else:
                    for file in result.data.files:
                        to_delete.append(f"{path_without_star}/{file}")
        else:
            to_delete.append(args.source)

        for file in to_delete:
            result = stat(file)

            if not result.success:
                return output(f"{__COMMAND__}: cannot find '{file}': No such file or directory", pipe, success=False)
            else:
                if not result.data.st_isfile and not args.recursive:
                    return output(f"{__COMMAND__}: cannot remove '{file}': Is a directory", pipe, success=False)
                else:
                    response = unlink(args.source)

                    if not response.success:
                        if response.message == ResultMessages.NOT_ALLOWED:
                            return output(f"{__COMMAND__}: cannot remove '{file}': Permission denied", pipe,
                                          success=False)
                    else:
                        if args.verbose:
                            print(f"removed '{file}'")

        return output("", pipe)
