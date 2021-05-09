from getpass import getpass
from hashlib import md5

from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.pwd import putpwent, passwd
from ..lib.unistd import getuid, get_user

__COMMAND__ = "passwd"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.1"


# TODO: We-write this so its not shit

def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("user", nargs="?")
    parser.add_argument("-p", dest="password")
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

        password = args.password if args.password else None

        if not args.user:
            # User just typed `passwd` (change current user password)
            user_to_change = get_user(uid=getuid()).data
        else:
            user_to_change = get_user(username=args.user)
            if not user_to_change.success:
                return output(f"{__COMMAND__}: user '{args[0]}' does not exist", pipe, success=False)

            user_to_change = user_to_change.data

        if user_to_change.password:
            # If the given user has a password, we need to know their password before changing
            print(f"Changing password for {user_to_change.username}")
            current_password = getpass("Current password: ")
            if md5(current_password.encode()).hexdigest() != user_to_change.password:
                return output(
                    f"{__COMMAND__}: Authentication token manipulation error\n{__COMMAND__}: password unchanged",
                    pipe, success=False)
            else:
                for _ in range(3):
                    if not password:
                        new_password = getpass("New password: ")
                        if not new_password:
                            print("No password supplied")
                        else:
                            confirm_new_password = getpass("Retype new password: ")
                            hashed_password = md5(new_password.encode()).hexdigest()
                            if new_password != confirm_new_password:
                                print("Sorry, passwords do not match.")
                                print(f"{__COMMAND__}: Authentication token manipulation error")
                                print(f"{__COMMAND__}: password unchanged")
                                break
                            elif hashed_password == user_to_change.password:
                                print("Password unchanged")
                            else:
                                password_struct = passwd(user_to_change.username, new_password, user_to_change.uid,
                                                         user_to_change.uid)
                                result = putpwent(password_struct)
                                if not result.success:
                                    return output(
                                        f"{__COMMAND__}: Failed to change password for user: '{user_to_change.username}'",
                                        pipe, success=False)
                                print(f"{__COMMAND__}: password updated successfully")
                                break
                    else:
                        hashed_password = md5(password.encode()).hexdigest()
                        if hashed_password == user_to_change.password:
                            print("Password unchanged")
                        else:
                            password_struct = passwd(user_to_change.username, password, user_to_change.uid,
                                                     user_to_change.uid)
                            result = putpwent(password_struct)
                            if not result.success:
                                return output(
                                    f"{__COMMAND__}: Failed to change password for user: '{user_to_change.username}'",
                                    pipe, success=False)
                            if result.success:
                                print(f"{__COMMAND__}: password updated successfully")
                            else:
                                return output(f"{__COMMAND__}: Failed to update password!", pipe, success=False)
                            break
        else:
            password_struct = passwd(user_to_change.username, password, user_to_change.uid,
                                     user_to_change.uid)
            result = putpwent(password_struct)
            if not result.success:
                return output(
                    f"{__COMMAND__}: Failed to change password for user: '{user_to_change.username}'",
                    pipe, success=False)

        return output("", pipe)
