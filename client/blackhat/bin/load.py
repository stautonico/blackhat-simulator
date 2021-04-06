from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "load"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("file")
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
        if not args.file.endswith(".save"):
            args.file += ".save"

        try:
            # Make sure the save location is readable
            with open(args.file, "r") as f:
                # Open the toload file which the game will load from
                with open("toload", "w") as load:
                    # Write the filename to load from
                    # The client checks if the 'toload' file has content which determines if we should load a game save or not
                    load.write(args.file)
            return output(f"Successfully loaded {args.file}. Please restart the game to load the save", pipe)
        except Exception as e:
            return output(f"{__COMMAND__}: Failed to load save: {args.file}", pipe, success=False)
