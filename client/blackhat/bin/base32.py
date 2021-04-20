from base64 import b32decode, b32encode
from binascii import Error

from ..computer import Computer
from ..fs import File
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "base32"
__DESCRIPTION__ = "base32 encode/decode data and print to standard output"
__VERSION__ = "1.2"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("files", nargs="+")
    parser.add_argument("-d", "--decode", action="store_true", help="decode data")
    parser.add_argument("-w", "--wrap", type=int,
                        help="wrap encoded lines after COLS character (default 76).  Use 0 to disable line wrapping")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION__}\n\n"

    for item in arg_helps:
        # Its a positional argument
        if len(item.option_strings) == 0:
            # If the argument is optional:
            if item.nargs == "?":
                SYNOPSIS += f"[{item.dest.upper()}] "
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


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    args, parser = parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # NOTE: This is an "improved" version that can handle multiple files at once
    # The real world version only does one file at a time
    # THIS IS SUBJECT TO CHANGE

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        output_text = ""
        for filename in args.files:
            find_file_result = computer.fs.find(filename)
            if not find_file_result.success:
                output_text += f"{__COMMAND__}: {filename}: No such file or directory\n"
            else:
                file: File = find_file_result.data
                if file.is_directory():
                    output_text += f"{__COMMAND__}: {filename}: Is a directory\n"
                else:
                    # We need read perms!
                    if not file.check_perm("read", computer).success:
                        output_text += f"{__COMMAND__}: {filename}: Permission denied\n"
                    else:
                        if args.decode:
                            try:
                                output_text += f"{file.name}: \n\n{b32decode(file.content.encode()).decode()}\n"
                            except Error:
                                output_text += f"{__COMMAND__}: {filename}: invalid input\n"
                        else:
                            output_text += f"{file.name}: \n\n{b32encode(file.content.encode()).decode()}\n"

        if args.wrap:
            if args.wrap == 0:
                output_text = output_text.strip("\n")
            else:
                wrapped_text = []
                for i in range(0, len(output_text), args.wrap):
                    wrapped_text.append(output_text[i:i + args.wrap])
                output_text = "\n".join(wrapped_text)

        return output(output_text, pipe)