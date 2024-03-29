__package__ = "blackhat.bin"

from getpass import getpass
from hashlib import md5

from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import getuid, get_user, new_session

__COMMAND__ = "su"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.1"


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
    parser.add_argument("user", nargs="?")
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
            return output(f"su from blackhat miscutils {__VERSION__}", pipe)

        # If we specific -h/--help, args will be empty, so exit gracefully
        if not args:
            return output("", pipe)
        else:
            if not args.user:
                to_login_as = "root"
            else:
                to_login_as = args.user

            # Check if the user exists
            user = None

            # Check if the given user exists
            user_lookup = get_user(username=to_login_as)
            if user_lookup.success:
                user = user_lookup.data
            else:
                return output(f"{__COMMAND__}: user {to_login_as} does not exist", pipe, success=False,
                              success_message=ResultMessages.NOT_FOUND)

            input_password = None

            # Authenticate
            if getuid() != 0:
                password = getpass()
                input_password = md5(password.encode()).hexdigest()

            if input_password == user.password or getuid() == 0:
                success = new_session(user.uid)
                if not success:
                    return output(f"{__COMMAND__}: Failed to create new session: Permission denied", pipe, success=False,
                                  success_message=ResultMessages.NOT_ALLOWED)

                return output("", pipe)
            else:
                return output(f"{__COMMAND__}: Authentication failure", pipe, success=False,
                              success_message=ResultMessages.NOT_ALLOWED)
