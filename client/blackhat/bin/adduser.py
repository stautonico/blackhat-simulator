from getpass import getpass

from ..computer import Computer
from ..fs import Directory
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "adduser"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("username")
    parser.add_argument("-p", dest="password")
    parser.add_argument("-n", dest="noninteractive", action="store_false")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.username:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:

        if computer.find_user(username=args.username).success:
            return output(f"{__COMMAND__}: The user '{args.username}' already exists.", pipe, success=False,
                          success_message=SysCallMessages.ALREADY_EXISTS)

        prev_uid = computer.get_all_users().data[-1].uid

        if prev_uid == 0:
            next_uid = 1000
        else:
            next_uid = prev_uid + 1

        if not args.password:
            if args.noninteractive:
                print(f"Adding user '{args.username}' ...")
                print(f"Adding new group '{args.username}' ({next_uid}) ...")
                print(f"Adding new user '{args.username}' ({next_uid}) with group '{args.username}' ...")
                print(f"Creating home directory '/home/{args.username}' ...")
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
            else:
                password = ""
        else:
            password = args.password

        user_result = computer.add_user(args.username, password)
        group_result = computer.add_group(args.username)
        # Find the user object and its its group to the new group
        computer.add_user_to_group(user_result.data, group_result.data, membership_type="primary")

        update_passwd_result = computer.update_user_and_group_files()
        update_group_result = computer.update_user_and_group_files()

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
            return output(f"{__COMMAND__}: /etc/skel is missing, unable to create user's home folder", pipe,
                          success=False)

        home_folder: Directory = home_folder_find.data
        skel_dir: Directory = skel_dir_find.data

        new_user_folder: Directory = Directory(args.username, home_folder, user_result.data, group_result.data)
        home_folder.add_file(new_user_folder)

        # Copy the contents of /etc/skel to the new users folder
        for file in skel_dir.files.values():
            computer.run_command("cp", [f"/etc/skel/{file.name}", f"/home/{args.username}/{file.name}", "-r"], pipe)

            computer.run_command("chmod", ["a-rwx", f"/home/{args.username}/{file.name}"], pipe)
            computer.run_command("chmod", ["u+rwx", f"/home/{args.username}/{file.name}"], pipe)
            # # Locate the new file and update the permissions
            # TODO: Replace this with the -R flag in chmod (recursive)
            new_file_find = computer.fs.find(f"/home/{args.username}/{file.name}")
            if new_file_find.success:
                computer.run_command("chmod", ["a-rwx", new_file_find.data.pwd()], pipe=False)
                computer.run_command("chmod", ["u+rwx", new_file_find.data.pwd()], pipe=False)

                # Change the file's owner (user and group)
                computer.run_command("chown",
                                     [f"{args.username}:{args.username}", f"/home/{args.username}/{file.name}"], pipe)

        # Write `export HOME=/home/args.username` and `export PATH=/bin:` to the new ~/.shellrc
        new_shellrc_result = computer.fs.find(f"/home/{args.username}/.shellrc")

        if new_shellrc_result.success:
            new_shellrc_result.data.write(f"export PATH=/bin:\nexport HOME=/home/{args.username}", computer)

        # Check if we should ask the user for Full name, etc
        if args.noninteractive:
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
