from ..computer import Computer
from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import read

__COMMAND__ = "cat"
__VERSION__ = "1=2.0"


def main(args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        output_text = ""

        for file in args.files:
            try_read = read(file)

            if not try_read.success:
                if try_read.message == ResultMessages.NOT_FOUND:
                    output_text += f"{__COMMAND__}: {file}: No such file or directory\n"
                elif try_read.message == ResultMessages.IS_DIRECTORY:
                    output_text += f"{__COMMAND__}: {file}: Is a directory\n"
                elif try_read.message == ResultMessages.NOT_ALLOWED_READ:
                    output_text += f"{__COMMAND__}: {file}: Permission denied\n"
            else:
                # Make sure they're are no extra \n at the end
                if try_read.data.endswith("\n"):
                    try_read.data = try_read.data[:-1]
                output_text += try_read.data
        return output(output_text, pipe)
