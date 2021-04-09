from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

from colorama import Fore, Style

__COMMAND__ = "ls"
__VERSION__ = "1.1"

def calculate_permission_string(fileobj):
    # Permission format
    # 0 - owner read
    # 1 - owner write
    # 2 - owner execute
    # 3 - group read
    # 4 - group write
    # 5 - group execute
    # 6 - public read
    # 7 - public write
    # 8 - public execute
    permissions = ["-", "-", "-", "-", "-", "-", "-", "-", "-"]
    # Owner read
    if "owner" in fileobj.permissions["read"]:
        permissions[0] = "r"

    # Owner write
    if "owner" in fileobj.permissions["write"]:
        permissions[1] = "w"

    # Owner execute
    if "owner" in fileobj.permissions["execute"]:
        permissions[2] = "x"

    # Group read
    if "group" in fileobj.permissions["read"]:
        permissions[3] = "r"

    # Group write
    if "group" in fileobj.permissions["write"]:
        permissions[4] = "w"

    # Group execute
    if "group" in fileobj.permissions["execute"]:
        permissions[5] = "x"

    # Public read
    if "public" in fileobj.permissions["read"]:
        permissions[6] = "r"

    # Public write
    if "public" in fileobj.permissions["write"]:
        permissions[7] = "w"

    # Public execute
    if "public" in fileobj.permissions["execute"]:
        permissions[8] = "x"

    return "".join(permissions)

def calculate_output(directory, computer, all=False, long=False):
    output_text = ""
    # Output a file (only show that one thing)
    if directory.is_file():
        if directory.name.startswith(".") and not all:
            return None
        else:
            if long:
                # Find the owner's username by uid and group name by gid
                username_lookup = computer.find_user(uid=directory.owner)
                group_lookup = computer.find_group(gid=directory.group_owner)

                username = username_lookup.data.username if username_lookup.success else "?"
                group_name = group_lookup.data.name if group_lookup.success else "?"
                output_text += f'{calculate_permission_string(directory)} {username} {group_name} {round(directory.size, 1)}kB {Fore.LIGHTBLUE_EX}{directory.name}{Style.RESET_ALL}\n'
            else:
                output_text += directory.name
    else:
        for file in directory.files.values():
            if file.name.startswith(".") and not all:
                pass
            else:
                if long:
                    # Find the owner's username by uid and group name by gid
                    username_lookup = computer.find_user(uid=file.owner)
                    group_lookup = computer.find_group(gid=file.group_owner)

                    username = username_lookup.data.username if username_lookup.success else "?"
                    group_name = group_lookup.data.name if group_lookup.success else "?"

                    if file.is_file():
                        output_text += f'{calculate_permission_string(file)} {username} {group_name} {round(file.size, 1)}kB {file.name}\n'
                    else:
                        output_text += f'{calculate_permission_string(file)} {username} {group_name} {round(file.size, 1)}kB {Fore.LIGHTBLUE_EX}{file.name}{Style.RESET_ALL}\n'
                else:
                    if file.is_file():
                        output_text += f"{file.name} "
                    else:
                        output_text += f"{Fore.LIGHTBLUE_EX}{file.name}{Style.RESET_ALL} "
    return output_text

def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """

    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("files", nargs="+", default=".")
    parser.add_argument("-a", dest="all", action="store_true")
    parser.add_argument("-l", dest="long", action="store_true")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        output_text = ""
        if len(args.files) > 0:

            for file in args.files:

                response = computer.fs.find(file)

                if response.success:
                    if len(args.files) > 1:
                        if response.data.is_directory():
                            output_text += f"{file}: \n"
                    output_text += calculate_output(response.data, computer, all=args.all, long=args.long) + "\n\n"
                else:
                    output_text += f"cannot access '{file}': No such file or directory\n\n"

        # No file args were specified (so print the local dir)
        else:
            response = computer.fs.find(".")

            if response.success:
                output_text = calculate_output(response.data, computer, all=args.all, long=args.long)
            else:
                return output("Error", pipe, success=False, success_message=SysCallMessages.NOT_FOUND)

        if not output_text:
            return output("", pipe)
        else:

            return output(output_text, pipe)

