__package__ = "blackhat.bin"

from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.sys.stat import stat
from ..lib.unistd import get_user, get_group, chown

__COMMAND__ = "chown"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.1"


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
    parser.add_argument("owner")
    parser.add_argument("file")
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
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.owner and not args.file:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        group_owner = None

        if ":" in args.owner:
            params_split = args.owner.split(":")
            owner = params_split[0]
            group_owner = params_split[1]
        else:
            owner = args.owner

        check_user_exists = get_user(username=owner)

        if not check_user_exists.success:
            return output(f"{__COMMAND__}: invalid user: {owner}", pipe, success=False)
        else:
            # Get the user object (because owner is the username (string))
            owner = check_user_exists.data.uid

        # Make sure the group exists (if we're using it)
        if group_owner:
            check_group_exists = get_group(name=group_owner)
            if not check_group_exists.success:
                return output(f"{__COMMAND__}: invalid group: {group_owner}", pipe, success=False)
            else:
                group_owner = check_group_exists.data.gid

        result = stat(args.file)

        if result.success:
            # Check if the dir we're trying to change is the root dir (we cant change perm)
            if result.data.st_path == "/":
                return output(f"{__COMMAND__}: Can't change owner of /", pipe, success=False)
            else:
                # Syscall
                update_response = chown(args.file, owner, group_owner)
                if not update_response.success:
                    if update_response.message == ResultMessages.NOT_ALLOWED:
                        return output(
                            f"{__COMMAND__}: changing ownership of '{args.file}': Operation not permitted",
                            pipe,
                            success=False)
                    else:
                        return output(
                            f"{__COMMAND__}: changing ownership of '{args.file}': Failed to change", pipe,
                            success=False)
        else:
            return output(f"{__COMMAND__}: cannot access '{args.file}': No such file or directory", pipe,
                          success=False)

    return output("", pipe)
