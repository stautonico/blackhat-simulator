from getpass import getpass
from hashlib import md5

from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "su"
__VERSION__ = "1.1"

from ..session import Session


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("user", nargs="?")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

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
        user_lookup = computer.find_user(username=to_login_as)
        if user_lookup.success:
            user = user_lookup.data
        else:
            return output(f"{__COMMAND__}: user {args[0]} does not exist", pipe, success=False,
                          success_message=SysCallMessages.NOT_FOUND)

        # Authenticate
        if computer.get_uid() != 0:
            password = getpass()
            input_password = md5(password.encode()).hexdigest()
        else:
            # Manually reset the effective UID (since we're changing sessions, sudo never resets it)
            computer.sessions[-1].effective_uid = computer.sessions[-1].real_uid
            input_password = computer.find_user(uid=0).data.password

        if input_password == user.password:
            current_session: Session = computer.sessions[-1]
            # Create a new session
            new_session = Session(user.uid, current_session.current_dir, current_session.id + 1)
            computer.sessions.append(new_session)
            computer.run_current_user_shellrc()

            return output("", pipe)
        else:
            return output(f"{__COMMAND__}: Authentication failure", pipe, success=False,
                          success_message=SysCallMessages.NOT_ALLOWED)
