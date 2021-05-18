from hashlib import md5

from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import read

__COMMAND__ = "md5sum"
__DESCRIPTION__ = "compute and check MD5 message digest"
__DESCRIPTION_LONG__ = "Print or check MD5 (128-bit) checksums."
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
    parser.add_argument("files", nargs="+")
    parser.add_argument("--tag", action="store_true", help="create a BSD-style checksum")
    parser.add_argument("-z", "--zero", action="store_true", help="Remove newline from the end of the file")
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

        for filename in args.files:
            find_file_result = read(filename)
            if not find_file_result.success:
                if find_file_result.message == ResultMessages.NOT_FOUND:
                    output_text += f"{__COMMAND__}: {filename}: No such file or directory\n"
                elif find_file_result.message == ResultMessages.NOT_ALLOWED_READ:
                    output_text += f"{__COMMAND__}: {filename}: Permission denied\n"
                elif find_file_result.message == ResultMessages.IS_DIRECTORY:
                    output_text += f"{__COMMAND__}: {filename}: Is a directory\n"

            to_hash = find_file_result.data[:-1] if find_file_result.data.endswith(
                "\n") and args.zero else find_file_result.data
            hash = md5(to_hash.encode()).hexdigest()
            if args.tag:
                output_text += f"MD5 ({filename}) = {hash}\n"
            else:
                output_text += f"{hash}  {filename}\n"

        return output(output_text, pipe)

