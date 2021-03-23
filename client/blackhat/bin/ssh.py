from getpass import getpass
from hashlib import md5

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output
from ..session import Session

__COMMAND__ = "ssh"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: missing arguments", pipe, success=False)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    port = 22

    if "-p" in args:
        try:
            port = int(args[args.index("-p") + 1])
            # Remove the flag and arg from the args to prevent 'user -p does not exist'
            args.remove("-p")
            args.remove(str(port))
        except IndexError:
            return output(f"{__COMMAND__}: option requires an argument -- 'p'", pipe, success=False)

    split_args = args[0].split("@")

    if len(split_args) != 2:
        return output(f"{__COMMAND__}: Could not resolve hostname : Name or service not known", pipe, success=False)

    username = split_args[0]
    host = split_args[1]

    computer_result = computer.parent.find_client(host, port=port)

    if not computer_result.success:
        return output(f"{__COMMAND__}: Could not resolve hostname {host}: Name or service not known", pipe,
                      success=False)

    # Double check that the computer has an ssh server running
    if port not in computer_result.data.services:
        return output(f"{__COMMAND__}: connect to host {host} port {port}: Connection refused", pipe,
                      success=False)

    # Try to get the user from the remote computer
    user_result = computer_result.data.find_user(username=username)

    # If we found the host, let's try to authenticate with the given host
    for x in range(3):
        password = getpass(f"{args[0]}'s password: ")

        hashed_password = md5(password.encode()).hexdigest()

        if user_result.success:
            if user_result.data.password == hashed_password:
                computer.shell.computers.append(computer_result.data)

                computer_result.data.shell = computer.shell

                if len(computer_result.data.sessions) == 0:
                    new_session = Session(user_result.data.uid, computer_result.data.fs.files, 0)
                else:
                    new_session = Session(user_result.data.uid, computer_result.data.fs.files,
                                          computer_result.data.sessions[-1].id + 1)

                computer_result.data.sessions.append(new_session)

                computer_result.data.run_current_user_shellrc()
                computer_result.data.run_command("cd", ["~"], False)
                return output("", pipe)

        print(f"Permission denied, please try again.")

    # PS1=\u@\h@\w\$:

    return output(f"{args[0]}: Permission denied (password).", pipe, success=False)
