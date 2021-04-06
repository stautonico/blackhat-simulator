import os

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "save"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("file", nargs="?")
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
        output_file = args.file if args.file else "blackhat.save"

        # We're going to temporarily disable debug mode (for manual saving)
        prev_debug_mode = os.environ.get("DEBUGMODE", "false")
        os.environ["DEBUGMODE"] = "false"
        save_result = computer.save(output_file)
        # Restore to what it was before after saving
        os.environ["DEBUGMODE"] = prev_debug_mode

        if not save_result:
            return output(f"{__COMMAND__}: Failed to save!", pipe, success=False)

        return output(f"{__COMMAND__}: Successfully saved to {output_file}!", pipe)
