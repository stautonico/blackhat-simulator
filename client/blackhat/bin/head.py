from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "head"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
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
            to_read_result = computer.fs.find(file)

            if not to_read_result.success:
                if to_read_result.message == SysCallMessages.NOT_FOUND:
                    output_text += f"{__COMMAND__}: {file}: No such file or directory\n"
                else:
                    output_text += f"{__COMMAND__}: Failed to read file\n"

            else:
                to_read = to_read_result.data

                if to_read.is_directory():
                    output_text += f"{__COMMAND__}: {file}: Is a directory\n"
                else:
                    # Permission checking
                    read_response = to_read.read(computer)

                    if read_response.success:
                        if read_response.data:
                            # Make sure they're are no extra \n at the end
                            if read_response.data.endswith("\n"):
                                read_response.data = read_response.data[:-1]

                        data = read_response.data.split("\n")
                        data = "\n".join(data[0:10])
                        output_text += data
                    else:
                        if read_response.message == SysCallMessages.NOT_ALLOWED:
                            output_text += f"{__COMMAND__}: {to_read.name}: Permission denied\n"

        return output(output_text, pipe)

