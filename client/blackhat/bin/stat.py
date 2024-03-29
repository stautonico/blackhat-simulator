__package__ = "blackhat.bin"

from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.sys.stat import stat
from ..lib.unistd import get_user, get_group

__COMMAND__ = "stat"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.0"


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
    parser.add_argument("file")
    parser.add_argument("--version", action="store_true", help=f"print program version")

    args = parser.parse_args(args)

    if not doc:
        return args, parser

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION_LONG__}\n\n"

    for item in arg_helps:
        # it's a positional argument
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

    return f"{NAME}\n\n{SYNOPSIS}\n\n{DESCRIPTION}\n\n"


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

        stat_file = stat(args.file)

        if not stat_file.success:
            return output(f"{__COMMAND__}: cannot stat '{args.file}': No such file or directory", pipe, success=False)

        stat_struct = stat_file.data

        lookup_username = get_user(uid=stat_struct.st_uid)
        lookup_group = get_group(gid=stat_struct.st_gid)
        username = lookup_username.data.username if lookup_username.success else "?"
        group = lookup_group.data.name if lookup_group.success else "?"

        output_text = ""

        output_text += f"File: {args.file}\n"
        output_text += f"Size: {stat_struct.st_size}\t{'regular file' if stat_struct.st_isfile else 'directory'}\n"
        # TODO: Links
        output_text += f"Links: 0\n"
        output_text += f"Access: ({stat_struct.st_mode})\tUid: ({stat_struct.st_uid}/{username})\tGid: ({stat_struct.st_gid}/{group})\n"
        output_text += f"Access: Not Yet Implemented\n"
        output_text += f"Modify: Not Yet Implemented\n"
        output_text += f"Change: Not Yet Implemented\n"

        return output(output_text, pipe)
