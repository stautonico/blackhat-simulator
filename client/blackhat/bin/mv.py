from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output
from .cp import copy

__COMMAND__ = "mv"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("source")
    parser.add_argument("destination")
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
        src_result = computer.fs.find(args.source)

        if not src_result.success:
            return output(f"{__COMMAND__}: cannot find '{args.source}': No such file or directory", pipe, success=False)
        else:
            # Make sure we have proper permissions before copying
            if src_result.data.check_perm("read", computer).success and src_result.data.check_perm(
                    "write", computer).success:
                copy_result = copy(computer, src_result.data, args.destination, True, args.verbose)

                if not copy_result.success:
                    if copy_result.message == SysCallMessages.NOT_FOUND:
                        return output(f"{__COMMAND__}: cannot find '{args.destination}': No such file or directory", pipe,
                                      success=False)
                    elif copy_result.message == SysCallMessages.GENERIC:
                        return output(f"{__COMMAND__}: invalid destination '{args.destination}'", pipe, success=False)
                    elif copy_result.message == SysCallMessages.NOT_ALLOWED_READ:
                        return output(f"{__COMMAND__}: cannot open '{args.source}' for reading: Permission denied", pipe,
                                      success=False)
                    elif copy_result.message == SysCallMessages.NOT_ALLOWED_WRITE:
                        return output(f"{__COMMAND__}: cannot open '{args.destination} for writing: Permission denied", pipe,
                                      success=False)
                    elif copy_result.message == SysCallMessages.ALREADY_EXISTS:
                        return output(f"{__COMMAND__}: cannot write '{args.destination}: Directory already exists", pipe,
                                      success=False)
                else:
                    computer.run_command("rm", [args.source, "-r"], pipe)
                    if args.verbose:
                        print(f"{args.source} -> {args.destination}")
                    return output("", pipe)
            else:
                return output(f"{__COMMAND__}: cannot open '{args.source}': Permission denied", pipe, success=False)

