from ..computer import Computer
from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "cd"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("directory")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.directory:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        response = computer.fs.find(args.directory)

        if response.success:
            if response.data.is_file():
                return output(f"{__COMMAND__}: not a directory: {args.directory}", pipe, success=False,
                              success_message=ResultMessages.IS_FILE)
            else:
                computer.sessions[-1].current_dir = response.data
                return output("", pipe)
        else:
            return output(f"{__COMMAND__}: no such file or directory: {args.directory}", pipe, success=False,
                          success_message=ResultMessages.NOT_FOUND)
