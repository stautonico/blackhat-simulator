from getpass import getpass

from ...helpers import Result, ResultMessages
from ...lib.dirent import readdir
from ...lib.input import ArgParser
from ...lib.output import output
from ...lib.sys.stat import stat, mkdir
from ...lib.unistd import get_user, get_all_users, write, add_user, add_group, add_user_to_group

__COMMAND__ = "adduser"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "2.0"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("username", help="Username of the new user to add")
    parser.add_argument("-p", dest="password", help="Password for the new user")
    parser.add_argument("-n", dest="noninteractive", action="store_false", help="Don't ask for user input")
    parser.add_argument("--version", action="store_true", help=f"print program version")

    args = parser.parse_args(args)

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION_LONG__}\n\n"

    for item in arg_helps:
        # Its a positional argument
        if len(item.option_strings) == 0:
            # If the argument is optional:
            if item.nargs == "?":
                SYNOPSIS += f"[{item.dest.upper()}] "
            elif item.nargs == "+":
                SYNOPSIS += f"[{item.dest.upper()}]... "
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
    args, parser = parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if get_user(username=args.username).success:
            return output(f"{__COMMAND__}: The user '{args.username}' already exists.", pipe, success=False,
                          success_message=ResultMessages.ALREADY_EXISTS)

        prev_uid = get_all_users().data[-1].uid

        if prev_uid == 0:
            next_uid = 1000
        else:
            next_uid = prev_uid + 1
            user_with_next_uid = get_user(uid=next_uid)

            while user_with_next_uid.success:
                next_uid += 1
                user_with_next_uid = get_user(uid=next_uid)

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

        user_result = add_user(args.username, password)
        group_result = add_group(args.username)
        # Find the user object and its its group to the new group
        add_user_to_group(user_result.data, group_result.data, membership_type="primary")

        # Create the users home directory (from /etc/skel)

        home_folder_find = stat("/home")
        skel_dir_find = stat("/etc/skel")

        if not home_folder_find.success:
            return output(f"{__COMMAND__}: /home is missing, unable to create user's home folder", pipe, success=False)

        if not skel_dir_find.success:
            return output(f"{__COMMAND__}: /etc/skel is missing, unable to create user's home folder", pipe,
                          success=False)

        mkdir(f"/home/{args.username}", 0o700)

        # Just make sure we can read /etc/skel (even tho we should be root)
        skel_read = readdir("/etc/skel")

        if not skel_read.success:
            print(f"{__COMMAND__}: Failed to read /etc/skel, unable to create user's home folder")
        else:

            # Copy the contents of /etc/skel to the new users folder
            # for file in skel_read.data:
            # TODO: DO this
            # computer.run_command("cp", [f"/etc/skel/{file.name}", f"/home/{args.username}/{file.name}", "-r"], pipe)
            #
            # computer.run_command("chmod", ["a-rwx", f"/home/{args.username}/{file.name}"], pipe)
            # computer.run_command("chmod", ["u+rwx", f"/home/{args.username}/{file.name}"], pipe)
            # # # Locate the new file and update the permissions
            # # TODO: Replace this with the -R flag in chmod (recursive)
            # new_file_find = computer.fs.find(f"/home/{args.username}/{file.name}")
            # if new_file_find.success:
            #     computer.run_command("chmod", ["a-rwx", new_file_find.data.pwd()], pipe=False)
            #     computer.run_command("chmod", ["u+rwx", new_file_find.data.pwd()], pipe=False)
            #
            #     # Change the file's owner (user and group)
            #     computer.run_command("chown",
            #                          [f"{args.username}:{args.username}", f"/home/{args.username}/{file.name}"], pipe)

            # Write `export HOME=/home/args.username` and `export PATH=/bin:` to the new ~/.shellrc
            new_shellrc_result = stat(f"/home/{args.username}/.shellrc")

            if new_shellrc_result.success:
                write(f"/home/{args.username}/.shellrc", f"export PATH=/bin:\nexport HOME=/home/{args.username}")

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

            if not stat("/etc/passwd").success:
                return output(f"{__COMMAND__}: /etc/passwd file missing! Cannot add new user", pipe, success=False)

        return output("", pipe)
