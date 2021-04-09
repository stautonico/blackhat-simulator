from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "commands"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
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

        try:
            bin_dirs_text = computer.sessions[-1].env.get("PATH").split(":")
            bin_dirs = []

            for dir in bin_dirs_text:
                find_dir = computer.fs.find(dir)
                if find_dir.success:
                    bin_dirs.append(find_dir.data)
        except AttributeError:
            find_bin = computer.fs.find("/bin")
            if find_bin.success:
                bin_dirs = [find_bin.data]
            else:
                bin_dirs = []

        for dir in bin_dirs:
            for command in list(dir.files.keys()):
                output_text += f"{command} "

        return output(output_text, pipe)
