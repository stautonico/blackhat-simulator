from getpass import getpass

from ..computer import Computer
from ..fs import Directory
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "adduser"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # Only root can add new users
    if computer.get_uid() != 0:
        return output(f"{__COMMAND__}: Only root may add a user or group to the system.", pipe, success=False)

    if len(args) == 0:
        return output(f"{__COMMAND__}: a username is required", pipe, success=False)

    password = None
    interactive = True

    # Check for non-interactive arg
    if "-n" in args:
        interactive = False
        args.remove("-n")
        # Make sure that the user specified -p with -n (a password is required for non-interactive mode)
        if "-p" not in args:
            return output(f"{__COMMAND__}: -p must be used with -n", pipe, success=False)

    if "-p" in args:
        try:
            password = args[args.index("-p") + 1]
            # Remove the flag and arg from the args to prevent 'user -p does not exist'
            args.remove("-p")
            args.remove(password)
        except IndexError:
            return output(f"{__COMMAND__}: option requires an argument -- 'p'", pipe, success=False)

    if computer.find_user(username=args[0]).success:
        return output(f"{__COMMAND__}: The user '{args[0]}' already exists.", pipe, success=False)

    prev_uid = computer.get_all_users().data[-1].uid

    if prev_uid == 0:
        next_uid = 1000
    else:
        next_uid = prev_uid + 1

    if not password:
        if interactive:
            print(f"Adding user '{args[0]}' ...")
            print(f"Adding new group '{args[0]}' ({next_uid}) ...")
            print(f"Adding new user '{args[0]}' ({next_uid}) with group '{args[0]}' ...")
            print(f"Creating home directory '/home/{args[0]}' ...")
            print(f"Copying files from '/etc/skel' ...")

        # Loop to try to get new password
        for _ in range(3):
            password = getpass("Enter new UNIX password: ")
            retype_new_password = getpass("Retype new UNIX password: ")

            if password != retype_new_password:
                print("Sorry, passwords do not match.")
                try_again = input("Try again? [y/N] ")
                if try_again != "y":
                    return output("", pipe, success=False)
            else:
                break
        # Fails password auth 3 times
        else:
            # Quit
            return output("", pipe)

    user_result = computer.add_user(args[0], password)
    group_result = computer.add_group(args[0])
    # Find the user object and its its group to the new group
    computer.add_user_to_group(user_result.data, group_result.data, membership_type="primary")

    update_passwd_result = computer.update_passwd()
    update_group_result = computer.update_groups()

    if not update_passwd_result.success:
        return output("passwd: Failed to update password", pipe, success=False)

    if not update_group_result.success:
        return output(f"passwd: Failed to update groups", pipe, success=False)

    # Create the users home directory (from /etc/skel)

    home_folder_find = computer.fs.find("/home")
    skel_dir_find = computer.fs.find("/etc/skel")

    if not home_folder_find.success:
        return output(f"{__COMMAND__}: /home is missing, unable to create user's home folder", pipe, success=False)

    if not skel_dir_find.success:
        return output(f"{__COMMAND__}: /etc/skel is missing, unable to create user's home folder", pipe, success=False)

    home_folder: Directory = home_folder_find.data
    skel_dir: Directory = skel_dir_find.data

    new_user_folder: Directory = Directory(args[0], home_folder, user_result.data, group_result.data)
    home_folder.add_file(new_user_folder)

    # Copy the contents of /etc/skel to the new users folder
    for file in skel_dir.files.values():
        computer.run_command("cp", [f"/etc/skel/{file.name}", f"/home/{args[0]}/{file.name}", "-r"], pipe)

        computer.run_command("chmod", ["a-rwx", f"/home/{args[0]}/{file.name}"], pipe)
        computer.run_command("chmod", ["u+rwx", f"/home/{args[0]}/{file.name}"], pipe)
        # # Locate the new file and update the permissions
        # TODO: Replace this with the -R flag in chmod (recursive)
        new_file_find = computer.fs.find(f"/home/{args[0]}/{file.name}")
        if new_file_find.success:
            computer.run_command("chmod", ["a-rwx", new_file_find.data.pwd()], pipe=False)
            computer.run_command("chmod", ["u+rwx", new_file_find.data.pwd()], pipe=False)

            # Change the file's owner (user and group)
            computer.run_command("chown", [f"{args[0]}:{args[0]}", f"/home/{args[0]}/{file.name}"], pipe)

    # Write `export HOME=/home/args[0]` and `export PATH=/bin:` to the new ~/.shellrc
    new_shellrc_result = computer.fs.find(f"/home/{args[0]}/.shellrc")

    if new_shellrc_result.success:
        new_shellrc_result.data.write(computer.get_uid(), f"export PATH=/bin:\nexport HOME=/home/{args[0]}", computer)

    # Check if we should ask the user for Full name, etc
    if interactive:
        while True:
            print("Enter the new value, or press ENTER for the default")
            full_name = input("\tFull Name []: ")
            room_num = input("\tRoom Number []: ")
            work_phone = input("\tWork Phone []: ")
            home_phone = input("\tHome Phone []: ")
            other = input("\tOther []: ")
            correct = input("Is the information correct? [Y/n] ")
            if correct in ["y", "Y", ""]:
                pass
                # computer.users[user_result.data].full_name = full_name
                # computer.users[user_result.data].room_number = room_num
                # computer.users[user_result.data].work_phone = work_phone
                # computer.users[user_result.data].home_phone = home_phone
                # computer.users[user_result.data].other = other
                break

    if not update_passwd_result.success:
        passwd_file = computer.fs.find("/etc/passwd")

        if not passwd_file.success:
            return output(f"{__COMMAND__}: /etc/passwd file missing! Cannot add new user", pipe, success=False)

    return output("", pipe)
