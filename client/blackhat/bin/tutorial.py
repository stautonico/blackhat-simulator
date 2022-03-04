__package__ = "blackhat.bin"

from colorama import Fore, Style

from ..helpers import Result
from ..lib.fcntl import creat
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.sys.stat import stat
from ..lib.unistd import write, read, getuid, get_user

__COMMAND__ = "tutorial"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.0"


def parse_args(args=None, doc=False):
    if args is None:
        args = []
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("--version", action="store_true", help=f"print program version")
    parser.add_argument("-r", dest="reset", action="store_true", help="Reset the tutorial")
    parser.add_argument("-c", dest="continuetutorial", action="store_true",
                        help="Continue the tutorial. Required for step 2 of the tutorial")

    args = parser.parse_args(args)

    if not doc:
        return args, parser

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION_LONG__}\n\n"

    for item in arg_helps:
        # it's a positional argument
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

    return f"{NAME}\n\n{SYNOPSIS}\n\n{DESCRIPTION}\n\n"


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

        progress = None

        stat_file = stat("/tmp/progress")

        if not stat_file.success:
            result = creat("/tmp/progress")

            if not result.success:
                return output(f"{__COMMAND__}: Cannot create temporary file", pipe, success=False)

            write_result = write("/tmp/progress", "1")

            if not write_result:
                return output(f"{__COMMAND__}: Cannot write to temporary file", pipe, success=False)

            progress = "1"
        else:
            read_result = read("/tmp/progress")
            if read_result:
                progress = read_result.data
            else:
                return output(f"{__COMMAND__}: Failed to read temporary file", pipe, success=False)

        if args.reset:
            write("/tmp/progress", "1")
            progress = "1"

    if args.continuetutorial:
        write("/tmp/progress", "2")
        progress = "2"


    if progress == "2":
        current_user = get_user(uid=getuid())
        stat_result = stat(f"/home/{current_user.data.username}/Documents/myfile")

        if stat_result.success:
            progress = "3"

    if progress == "1":
        print("Welcome to the Linux Simulator Training Program™")
        print("Press enter to continue after each line...")
        input()
        print("This program is designed to interactively teach you the basics of the linux terminal.")
        input()
        print("The way this executable works is by asking you to preform an action and quits.")
        input()
        print(
            "Once you preform that action, you should re-run this tutorial program and it will tell you what to do next")
        input()
        print("Navigating the file system using the terminal is similar to clicking on folders")
        input()
        print("You can view your current directory in the fs (file system) by looking at the prompt on your terminal")
        input()
        print(f"Another way of viewing your current directory is by typing '{Fore.LIGHTRED_EX}pwd{Style.RESET_ALL}'")
        input()
        print("As you can see, you're in your home folder. The home folder is a a folder that each user gets")
        print("This folder contains sub-folders such as: Desktop, Downloads, Pictures, etc.")
        input()
        print(f"You can list the files in your current directory by typing '{Fore.LIGHTRED_EX}ls{Style.RESET_ALL}'")
        input()
        print(
            "In a file browser, you can simply double click the folder however, through a terminal, its just a little different")
        input()
        print(
            f"To navigate to a directory, you can use the '{Fore.LIGHTRED_EX}cd{Style.RESET_ALL}' command (which stands for change directory).")
        input()
        print(
            f"For example, to view your downloads folder, you can type '{Fore.LIGHTRED_EX}cd Downloads{Style.RESET_ALL}'")
        input()
        print("The next significant part of running commands is passing options or arguments to commands")
        input()
        print("In the previous command ('cd Downloads'),  'cd' is the command and 'Downloads' is the argument")
        input()
        print("You can also pass other options (usually non-mandatory) to a command using flags.")
        print(
            f"For example, to view more stats about a file using ls, you can pass the '{Fore.LIGHTRED_EX}-l{Style.RESET_ALL}'")
        print(f"The {Fore.LIGHTRED_EX}-l{Style.RESET_ALL}' stands for 'long'")
        input()
        print(
            f"For the next stage, try calling the '{Fore.LIGHTRED_EX}tutorial{Style.RESET_ALL}' command while passing the '{Fore.LIGHTRED_EX}-c{Style.RESET_ALL}' flag")
        print("Which stands for continue. Without the -c flag, the tutorial will reset.")
        input()
        print(
            f"Note: '{Fore.LIGHTRED_EX}-c{Style.RESET_ALL}' is unique to this program. Each program has its own flags with their own meanings")
        input()
        print(f"Try it now!")
        input()
    elif progress == "2":
        print("Good job!")
        input()
        print(
            f"You can restart the progress of the tutorial at any time by calling the tutorial command with the '{Fore.LIGHTRED_EX}-r{Style.RESET_ALL}' flag")
        input()
        print("The next section will teach you how to create, remove, and modify files.")
        input()
        print(
            f"To create a new empty file, you can use the '{Fore.LIGHTRED_EX}touch{Style.RESET_ALL}' command and the file name.")
        input()
        print(
            f"Your next task is to create a new file called '{Fore.LIGHTRED_EX}myfile{Style.RESET_ALL}' in your '{Fore.LIGHTRED_EX}Documents{Style.RESET_ALL}' folder")
        input()
        print(f"Note: The next time you call tutorial, you {Fore.LIGHTRED_EX}don't{Style.RESET_ALL} need to include -c")
    elif progress == "3":
        print("Good!")
        print("This tutorial will be continued soon!")
        input()


    return output("", pipe)
