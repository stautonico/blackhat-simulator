from asyncio import sleep
from getpass import getpass
from hashlib import md5

from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "sudo"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output(f"{__COMMAND__}: missing argument: command", pipe, success=False,
                      success_message=SysCallMessages.MISSING_ARGUMENT)

    if "-u" in args:
        try:
            user_run_as = args[args.index("-u") + 1]
            args.remove("-u")
            args.remove(user_run_as)

            user = None

            # Check if the given user exists
            for key, value in computer.users.items():
                if value.username == user_run_as:
                    user = value
                    break
            else:
                return output(f"{__COMMAND__}: unknown user: {user_run_as}", pipe, success=False,
                              success_message=SysCallMessages.NOT_FOUND)
        except IndexError:
            return output(f"{__COMMAND__}: option requires an argument -- 'u'", pipe, success=False,
                          success_message=SysCallMessages.MISSING_ARGUMENT)

    else:
        user = computer.users[0]

    # We need to authenticate as that user before we can run any commands
    for x in range(3):
        password = getpass()

        # Encode the password
        password = md5(password.encode()).hexdigest()

        if password == user.password:
            computer.sessions[-1].effective_uid = user.uid
            # args[0] : command
            # args[1:] : arguments
            result = computer.run_command(args[0], args[1:], pipe)
            # Reset the effective user after running command
            computer.sessions[-1].effective_uid = computer.sessions[-1].real_uid
            return result
        else:
            # Simulates the password checking delay when wrong password is entered
            sleep(0.25)
            if x != 2:
                print("Sorry, try again.")

    return output(f"{__COMMAND__}: 3 incorrect password attempts", pipe, success=False,
                  success_message=SysCallMessages.NOT_ALLOWED)
