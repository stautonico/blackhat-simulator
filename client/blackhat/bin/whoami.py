from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "whoami"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__,
                       description="Print the user name associated with the current effective user ID.")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

        # TODO: Implement "extra operand" error

    if args.version:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        lookup_result: SysCallStatus = computer.find_user(computer.get_uid())

        if lookup_result.success:
            return output(lookup_result.data.username, pipe)
        else:
            return output(f"{__COMMAND__}: failed to find username for uid {computer.get_uid()}", pipe, success=False,
                          success_message=SysCallMessages.NOT_FOUND)
