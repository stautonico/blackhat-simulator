from getpass import getpass
from hashlib import md5

from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output
from ..session import Session

__COMMAND__ = "su"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        to_login_as = "root"
    else:
        to_login_as = args[0]

    # Check if the user exists
    user = None

    # Check if the given user exists
    for key, value in computer.users.items():
        if value.username == to_login_as:
            user = value
            break
    else:
        return output(f"{__COMMAND__}: user {args[0]} does not exist", pipe, success=False,
                      success_message=SysCallMessages.NOT_FOUND)

    # Authenticate
    password = getpass()

    if md5(password.encode()).hexdigest() == user.password:
        current_session: Session = computer.sessions[-1]
        # Create a new session
        new_session = Session(user.uid, current_session.current_dir, current_session.id + 1)
        computer.sessions.append(new_session)
        return output("", pipe)
    else:
        return output(f"{__COMMAND__}: Authentication failure", pipe, success=False,
                      success_message=SysCallMessages.NOT_ALLOWED)
