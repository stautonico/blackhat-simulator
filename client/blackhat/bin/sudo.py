__package__ = "blackhat.bin"

import datetime
from asyncio import sleep
from getpass import getpass
from hashlib import md5

from ..helpers import ResultMessages, Result
from ..lib.fcntl import creat
from ..lib.output import output
from ..lib.stdlib import get_env
from ..lib.sys.stat import stat
from ..lib.unistd import getuid, get_user, read, gethostname, setuid, execvp, write

__COMMAND__ = "sudo"
__VERSION__ = "1.1"


def run_as_user(args, user, current_user):
    # Save the current timestamp to /run/sudo/ts/USERNAME
    creat(f"/run/sudo/ts/{current_user.username}", 0o600)
    write(f"/run/sudo/ts/{current_user.username}", str(datetime.datetime.now().timestamp()))

    setuid(user.uid)
    # args[0] : command
    # args[1:] : arguments
    result = execvp(args[0], args[1:])
    # Reset the effective user after running command
    setuid(current_user.uid)
    return result


def main(args: list, pipe: bool) -> Result:
    # TODO: Find a way to do this with arg parser without it breaking lol
    if "--version" in args:
        return output(f"Sudo version {__VERSION__} (miscutils)", pipe)

    if len(args) == 0:
        return output(f"{__COMMAND__}: missing argument: command", pipe, success=False,
                      success_message=ResultMessages.MISSING_ARGUMENT)

    # We can't run sudo without the /etc/sudoers
    sudoers_file_result = read("/etc/sudoers")

    if not sudoers_file_result.success:
        if sudoers_file_result.message == ResultMessages.NOT_ALLOWED:
            return output(f"{__COMMAND__}: Cannot read sudoers file: Permission denied", pipe, success=False)

        return output(f"{__COMMAND__}: no valid sudoers sources found, quitting", pipe, success=False)

    sudoers_file = sudoers_file_result.data

    # Parse the sudoers index for the current user
    # First we want to get the username of the current uid

    user_lookup = get_user(uid=getuid())

    if user_lookup.success:
        username = user_lookup.data.username
    else:
        return output(f"{__COMMAND__}: cannot find user with UID {getuid()}", pipe, success=False)

    # We want to look for the -u before the command we're running
    # For example, if we use sudo with adduser -u, we get an invalid user error
    if "-u" in args:
        try:
            user_run_as = args[args.index("-u") + 1]
            args.remove("-u")
            args.remove(user_run_as)

            # Check if the given user exists
            user_lookup = get_user(username=user_run_as)

            if not user_lookup.success:
                return output(f"{__COMMAND__}: unknown user: {user_run_as}", pipe, success=False,
                              success_message=ResultMessages.NOT_FOUND)
            else:
                user = user_lookup.data
        except IndexError:
            return output(f"{__COMMAND__}: option requires an argument -- 'u'", pipe, success=False,
                          success_message=ResultMessages.MISSING_ARGUMENT)

    else:
        user = get_user(uid=0).data

    # We can't do a getuid() because this is a setuid binary and it'll always be root
    # Instead, we'll try to get the $USER environment variable
    # If it's not set, we'll crash
    username = get_env("USER")
    if not username:
        return output(f"{__COMMAND__}: cannot determine user", pipe, success=False)

    current_user = get_user(username=username).data

    # Check if we have a timeout for this user
    timeout_file = stat(f"/run/sudo/{current_user.username}")

    if timeout_file.success:
        # Check if the timeout is < 5 minutes
        timeout_data = read(f"/run/sudo/{current_user.username}")
        if timeout_data.success:
            timeout_timestamp = datetime.datetime.fromtimestamp(float(timeout_data.data))
            if timeout_timestamp + datetime.timedelta(minutes=5) > datetime.datetime.now():
                return run_as_user(args, user, current_user)

    # We need to authenticate as that user before we can run any commands
    for x in range(3):
        password = getpass()

        # Encode the password
        password = md5(password.encode()).hexdigest()

        if password == current_user.password:
            # Now lets isolate the record regarding this `username`
            split_sudoers_content = sudoers_file.split("\n")

            # NOTE: Possible exploit we're going to leave on purpose
            # Lets find the line that contains the username
            line = None
            for line in split_sudoers_content:
                if line.startswith(username):
                    break
            else:
                return output(f"{__COMMAND__}: {username} is not in the sudoers file. This incident will be reported",
                              pipe, success=False)

            # Now lets parse the line and determine what the users allowed to do
            # We don't care about the username because we already know who this line belongs to
            _username, line = line.split(" ", 1)

            # Current line format <HOST> = (<USERS>) <COMMANDS>
            # Lets extract the host and make sure it says "ALL" or our current hostname
            host, line = line.split("=", 1)
            if host.lower() != "all" and host != gethostname():
                return output(
                    f"{__COMMAND__}: user {username} is not allowed to use sudo on this host. This incident will be reported",
                    pipe, success=False)

            users, commands = line.split(")", 1)

            # We need to remove the extra "(" from the beginning of the users array and remove the extra spaces
            users = users.strip("(").split(",")
            users = [x.strip(" ") for x in users]
            commands = [x.strip(" ") for x in commands.split(",")]

            # Lets check if we're allowed to execute as the user
            for usr in users:
                if usr in ["ALL", user.username]:
                    break
            else:
                return output(
                    f"{__COMMAND__}: user {username} is not allowed to use sudo as user {user.username}. This incident will be reported",
                    pipe, success=False)

            # Lets check if we're allowed to execute the command
            for cmd in commands:
                if cmd in ["ALL", args[0]]:
                    break
            else:
                return output(
                    f"{__COMMAND__}: user {username} is not allowed to use sudo to execute {args[0]}. This incident will be reported",
                    pipe, success=False)

            return run_as_user(args, user, current_user)
        else:
            # Simulates the password checking delay when wrong password is entered
            sleep(0.25)
            if x != 2:
                print("Sorry, try again.")

    return output(f"{__COMMAND__}: 3 incorrect password attempts", pipe, success=False,
                  success_message=ResultMessages.NOT_ALLOWED)
