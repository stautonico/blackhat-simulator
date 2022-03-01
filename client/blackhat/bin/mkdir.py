__package__ = "blackhat.bin"

from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.sys.stat import mkdir, stat

__COMMAND__ = "mkdir"
__VERSION__ = "1.0"


def main(args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("directories", nargs="+")
    parser.add_argument("-p", dest="create_parents", action="store_true")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.directories:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        for filename in args.directories:
            if args.create_parents:
                # Split the path and make each directory
                path = filename.split("/")

                for x in range(len(path)+1):
                    current_path = "/".join(path[0:x])
                    current_item = stat(current_path)
                    if not current_item.success:
                        result = mkdir(current_path)
                        if not result.success:
                            return output(f"{__COMMAND__}: Failed to create parent path", pipe, success=False)
            else:
                result = mkdir(filename)
                if not result.success:
                    print(f"{__COMMAND__}: Error: {result.message}")
    return output("", pipe)
