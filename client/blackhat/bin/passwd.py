from getpass import getpass
from hashlib import md5

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "passwd"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    password = None
    passwd_file = computer.fs.find("/etc/passwd")

    if not passwd_file.success:
        return output(f"{__COMMAND__}: Cannot update password, missing /etc/passwd", pipe, success=False)
    else:
        passwd_file = passwd_file.data

    if "-p" in args:
        try:
            password = args[args.index("-p") + 1]
            # Remove the flag and arg from the args to prevent 'user -p does not exist'
            args.remove("-p")
            args.remove(password)
        except IndexError:
            return output(f"{__COMMAND__}: option requires an argument -- 'p'", pipe, success=False)

    if len(args) == 0:
        # User just typed `passwd` (change current user password)
        user_to_change = computer.find_user(uid=computer.get_uid()).data
    else:
        user_to_change = computer.find_user(username=args[0])
        if not user_to_change.success:
            return output(f"{__COMMAND__}: user '{args[0]}' does not exist", pipe, success=False)

        user_to_change = user_to_change.data

    if user_to_change.password:
        # If the given user has a password, we need to know their password before changing
        print(f"Changing password for {user_to_change.username}")
        current_password = getpass("Current password: ")
        if md5(current_password.encode()).hexdigest() != user_to_change.password:
            return output(f"{__COMMAND__}: Authentication token manipulation error\n{__COMMAND__}: password unchanged",
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
                            computer.change_user_password(user_to_change.uid, new_password)
                            print(f"{__COMMAND__}: password updated successfully")
                            break
                else:
                    hashed_password = md5(password.encode()).hexdigest()
                    if hashed_password == user_to_change.password:
                        print("Password unchanged")
                    else:
                        result = computer.change_user_password(user_to_change.uid, password)
                        if result.success:
                            print(f"{__COMMAND__}: password updated successfully")
                        else:
                            return output(f"{__COMMAND__}: Failed to update password!", pipe, success=False)
                        break
    else:
        computer.change_user_password(user_to_change.uid, password)

    computer.update_passwd()

    return output("", pipe)
