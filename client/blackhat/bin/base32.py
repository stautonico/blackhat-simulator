from base64 import b32decode, b32encode
from binascii import Error

from ..computer import Computer
from ..fs import File
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "base32"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("-d", "--decode", action="store_true")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

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

        return output(output_text, pipe)
