from hashlib import sha1

from ..computer import Computer
from ..fs import File
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "sha1sum"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

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

        for filename in args.files:
            find_file_result = computer.fs.find(filename)
            if not find_file_result.success:
                output_text += f"{filename}: No such file or directory\n"
            else:
                file: File = find_file_result.data
                if file.is_directory():
                    output_text += f"{filename}: Is a directory\n"
                else:
                    # We need read perms!
                    if not file.check_perm("read", computer).success:
                        output_text += f"{filename}: Permission denied\n"
                    else:
                        hash = sha1(file.content.encode()).hexdigest()
                        output_text += f"{hash}  {filename}\n"

        return output(output_text, pipe)
