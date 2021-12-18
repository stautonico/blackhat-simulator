__package__ = "blackhat.bin"

import os

from colorama import Fore, Style

from ..helpers import Result
from ..helpers import stat_struct
from ..lib.dirent import readdir
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.sys.stat import stat
from ..lib.unistd import get_user, get_group

__COMMAND__ = "ls"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "2.0"


def parse_args(args=[], doc=False):
    """
    Handle parsing of arguments and flags. Generates docs using help from `ArgParser`

    Args:
        args (list): argv passed to the binary
        doc (bool): If the function should generate and return manpage

    Returns:
        Processed args and a copy of the `ArgParser` object if not `doc` else a `string` containing the generated manpage
    """
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("files", nargs="*", default=".")
    parser.add_argument("-a", dest="all", action="store_true")
    parser.add_argument("-l", dest="long", action="store_true")
    parser.add_argument("--no-color", dest="nocolor", action="store_true")
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


def calculate_permission_string(perm_octal: int) -> str:
    perms = {
        "0": "---",
        "1": "--x",
        "2": "-w-",
        "3": "-wx",
        "4": "r--",
        "5": "r-x",
        "6": "rw-",
        "7": "rwx"
    }

    result = ""

    for bit in str(perm_octal):
        result += perms[bit]

    return result


def calculate_output(filename, file_struct: stat_struct, long=False, nocolor=False):
    output_text = ""

    base_filename = filename.split("/")[-1]
    color = Fore.WHITE if file_struct.st_isfile or nocolor else Fore.LIGHTBLUE_EX

    if long:
        username_lookup = get_user(uid=file_struct.st_uid)
        group_lookup = get_group(gid=file_struct.st_gid)

        username = username_lookup.data.username if username_lookup.success else "?"
        group_name = group_lookup.data.name if group_lookup.success else "?"

        file_size_in_kb = round(file_struct.st_size / 1024, 1)

        output_text += f'{calculate_permission_string(file_struct.st_mode)} {username} {group_name} {file_size_in_kb}kB {color}{base_filename}{Style.RESET_ALL}\n'
    else:
        output_text += f"{color}{base_filename}{Style.RESET_ALL} "

    return output_text


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

        output_text = ""

        if len(args.files) > 0 and args.files != ".":
            to_list = args.files

        # No file args were specified (so print the local dir)
        else:
            to_list = ["."]

        for file in to_list:
            stat_result = stat(file)

            if not stat_result.success:
                output_text += f"{__COMMAND__}: Cannot stat file: {file}\n"
                continue

            if stat_result.data.st_isfile:
                output_text += calculate_output(file, stat_result.data, args.long, args.nocolor)
            else:
                read_result = readdir(file)

                for subfile in read_result.data:
                    if args.all or not subfile.startswith("."):
                        stat_result = stat(os.path.join(file, subfile))
                        if not stat_result.success:
                            output_text += f"{__COMMAND__}: Cannot stat file: {file}\n"
                        else:
                            output_text += calculate_output(subfile, stat_result.data, args.long, args.nocolor)

        if not output_text:
            return output("", pipe)
        else:
            return output(output_text, pipe)
