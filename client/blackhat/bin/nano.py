from os import system, remove
from secrets import token_hex

from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import read, write
from ..lib.sys.stat import stat
from ..lib.fcntl import creat

__COMMAND__ = "nano"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.1"


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
    parser.add_argument("-p", "--poweroff", action="store_true",
                        help="Power-off the machine, regardless of which one of the two commands is invoked.")
    parser.add_argument("--reboot", action="store_true",
                        help="Reboot the machine, regardless of which one of the three commands is invoked.")

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
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("source")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    if args.version:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        source_path = "./" + args.source if "/" not in args.source else args.source

        find_response = stat(source_path)

        if not find_response.success:
            find_response = stat("/".join(args.source.split("/")[:-1]))
            if not find_response.success:
                return output(f"{__COMMAND__}: No such file or directory", pipe, success=False)
            else:
                # Create the new file
                create_file_response = creat(source_path, 0o644)
                if not create_file_response.success:
                    return output(f"{__COMMAND__}: Unable to create file: {args.source}", pipe, success=False)
                else:
                    file_to_write = stat(args.source).data

        else:
            # If this exists, the file already existed, we can read its contents
            # and write it into the physical file
            exists = True
            file_to_write = find_response.data

        if not file_to_write.st_isfile:
            return output(f"{__COMMAND__}: {args.source}: Is a directory", pipe, success=False)

        read_file_result = read(source_path)

        if not read_file_result.success:
            return output(f"{__COMMAND__}: {args.source}: Permission denied", pipe, success=False)

        # Create a temporary dir in the real /tmp to write to and read from because im not re-writing nano from scratch
        # for this dumb ass game
        temp_file = token_hex(6)

        try:
            if exists:
                with open(f"/tmp/{temp_file}", "w") as f:
                    f.write(read_file_result.data)

            system(f"nano /tmp/{temp_file}")

            with open(f"/tmp/{temp_file}", "r") as f:
                file_content = f.read()

            remove(f"/tmp/{temp_file}")

            write_result = write(source_path, file_content)

            if not write_result.success:
                return output(f"{__COMMAND__}: {args.source}: Permission denied", pipe, success=False)

            return output("", pipe)

        except Exception as e:
            return output(f"{__COMMAND__}: Failed to write file!", pipe, success=False)
