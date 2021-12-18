__package__ = "blackhat.bin"

from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import read
from ..lib.sys.stat import stat

__COMMAND__ = "wc"
__DESCRIPTION__ = "print newline, word, and byte counts for each file"
__DESCRIPTION_LONG__ = """Print newline, word, and byte counts for each FILE, and a total line if more than one FILE is specified.  A word is a non-zero-length sequence of characters delimited by white space.\n\n\tThe options below may be used to select which counts are printed, always in the following order: newline, word,  character,  byte,  maximum  line
length."""
__VERSION__ = "1.2"


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
    parser.add_argument("file", nargs="+")
    parser.add_argument("-c", "--bytes", action="store_true", help="print the byte counts")
    parser.add_argument("-m", "--chars", action="store_true", help="print the character counts")
    parser.add_argument("-l", "--lines", action="store_true", help="print the newline counts")
    parser.add_argument("-L", "--max-line-length", dest="maxlinelength", action="store_true",
                        help="print the maximum display width")
    parser.add_argument("-w", "--words", action="store_true", help="print the word counts")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

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

        output_text = ""

        total_new_line_count = 0
        total_word_count = 0
        total_byte_count = 0

        # TODO: Allow cat <FILE> | wc
        for file in args.file:
            find_file = stat(file)
            if not find_file.success:
                output_text += f"{__COMMAND__}: '{file}': No such file or directory\n"
                continue


            if not find_file.data.st_isfile:
                output_text += f"{__COMMAND__}: '{file}': Is a directory\n"
                continue

            try_read_file = read(file)

            if not try_read_file.success:
                output_text += f"{__COMMAND__}: '{file}': Permission denied\n"
                continue

            new_line_count = try_read_file.data.count("\n")
            word_count = len(try_read_file.data.split(" "))
            byte_count = len(try_read_file.data)

            total_new_line_count += new_line_count
            total_word_count += word_count
            total_byte_count += byte_count

            # Default option
            if not args.bytes and not args.chars and not args.lines and not args.maxlinelength and not args.words:
                output_text += f"{new_line_count} {word_count}  {byte_count} {file}\n"
                continue

            # Order of flags should be: newline, word, chracter, byte, maximum line length

            if args.lines:
                output_text += f"{new_line_count} "

            if args.words:
                output_text += f"{word_count} "

            if args.chars:
                output_text += f"{byte_count} "

            if args.bytes:
                output_text += f"{byte_count} "

            if args.maxlinelength:
                max_line_length = 0
                for item in try_read_file.data.split("\n"):
                    if len(item) > max_line_length:
                        max_line_length = len(item)

                output_text += f"{max_line_length} "

            output_text += f"{file}\n"

        if len(args.file) > 1:
            output_text += f"{total_new_line_count} {total_word_count} {total_byte_count} total"

        return output(output_text, pipe)
