__package__ = "blackhat.bin.installable"

from ...helpers import Result
from ...lib.input import ArgParser
from ...lib.output import output
from ...lib.sys.stat import stat
from ...lib.unistd import read

__COMMAND__ = "unshadow"
__DESCRIPTION__ = "Combines a passwd file and shadow file for cracking with john"
__DESCRIPTION_LONG__ = "Combines a passwd file and shadow file for cracking with john"
__VERSION__ = "1.0"


def parse_args(args=None, doc=False):
    """
    Handle parsing of arguments and flags. Generates docs using help from `ArgParser`

    Args:
        args (list): argv passed to the binary
        doc (bool): If the function should generate and return manpage

    Returns:
        Processed args and a copy of the `ArgParser` object if not `doc` else a `string` containing the generated manpage
    """
    if args is None:
        args = []
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("password", help="File containing usernames, usually /etc/passwd")
    parser.add_argument("shadow", help="File containing usernames and password hashes, usually /etc/shadow")
    parser.add_argument("--version", action="store_true", help=f"print program version")

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
            return output(f"Usage: {__COMMAND__} PASSWORD-FILE SHADOW-FILE", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        # Try to open the given password and shadow file
        find_password_file = stat(args.password)
        find_shadow_file = stat(args.shadow)

        if not find_password_file.success:
            return output(f"{__COMMAND__}: {args.password}: No such file or directory", pipe, success=False)

        if not find_shadow_file.success:
            return output(f"{__COMMAND__}: {args.shadow}: No such file or directory", pipe, success=False)

        read_password_content = read(args.password)
        read_password_shadow = read(args.shadow)

        if not read_password_content.success:
            return output(f"{__COMMAND__}: {args.password}: Permission denied", pipe, success=False)

        if not read_password_shadow.success:
            return output(f"{__COMMAND__}: {args.shadow}: Permission denied", pipe, success=False)

        password_content = read_password_content.data.split("\n")
        shadow_content = read_password_shadow.data.split("\n")

        while "" in password_content:
            password_content.remove("")
        while "" in shadow_content:
            shadow_content.remove("")

        output_text = ""

        for line in password_content:
            split_line = line.split(":")
            # If the length of arguments isn't 4, we'll consider it an invalid line
            if len(split_line) != 4:
                continue

            username, password = split_line[0], split_line[1]

            if password == "x":
                # Now lets find the line in our shadow files that matches this user
                find_line_shadow = [i for i in shadow_content if i.startswith(username + ":")]
                if len(find_line_shadow) == 0:
                    continue

                split_shadow_line = find_line_shadow[0].split(":")
                # If the length of arguments isn't 2, we'll consider it an invalid line
                if len(split_shadow_line) != 2:
                    continue

                password = split_shadow_line[1]

            if password != "x":
                output_text += f"{username}:{password}\n"

        return output(output_text, pipe)
