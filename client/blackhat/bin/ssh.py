from getpass import getpass
from hashlib import md5

from ..computer import Computer
from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "ssh"
__VERSION__ = "1.1"

from ..session import Session


def main(computer: Computer, args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("host")
    parser.add_argument("-p", dest="port", default=22, type=int)
    parser.add_argument("--version", "-V", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    if args.version:
        return output(f"BlackhatSSH: {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        split_args = args.host.split("@")

        if len(split_args) != 2:
            return output(f"{__COMMAND__}: Could not resolve hostname : Name or service not known", pipe, success=False)

        username = split_args[0]
        host = split_args[1]

        computer_result = computer.parent.find_client(host, port=args.port)

        if not computer_result.success:
            return output(f"{__COMMAND__}: Could not resolve hostname {host}: Name or service not known", pipe,
                          success=False)

        # Double check that the computer has an ssh server running
        if args.port not in computer_result.data.services:
            return output(f"{__COMMAND__}: connect to host {host} port {args.port}: Connection refused", pipe,
                          success=False)

        # Try to get the user from the remote computer
        user_result = computer_result.data.get_user(username=username)

        # If we found the host, let's try to authenticate with the given host
        for x in range(3):
            password = getpass(f"{args.host}'s password: ")

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

        return output(f"{args.host}: Permission denied (password).", pipe, success=False)
