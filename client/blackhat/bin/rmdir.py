from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "rmdir"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("sources", nargs="+")
    parser.add_argument("-v", "--verbose", action="store_true")
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
        output_text = ""

        for file in args.sources:
            result = computer.fs.find(file)

            if not result.success:
                output_text += f"cannot find '{file}': No such file or directory\n"
                continue
            else:
                if result.data.is_file():
                    output_text += f"failed to remove '{file}': Not a directory\n"
                    continue
                else:
                    # rmdir only removes empty dirs
                    if len(result.data.files) > 0:
                        output_text += f"failed to remove '{file}': Directory not empty\n"
                        continue
                    else:
                        response = result.data.delete(computer)

                        if not response.success:
                            if response.message == SysCallMessages.NOT_ALLOWED:
                                output_text += f"cannot remove '{file}': Permission denied"
                                continue
            if args.verbose:
                output_text += f"removed '{file}'\n"

        return output(output_text, pipe)
