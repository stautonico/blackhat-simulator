from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "echo"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("string", nargs="+")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.string:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        clean_args = []

        # If the output starts with $, read from env vars
        for arg in args.string:
            if arg.startswith("$"):
                env_var = computer.get_env(arg.replace("$", ""))
                if env_var:
                    clean_args.append(env_var)
            else:
                clean_args.append(arg)

        return output(" ".join(clean_args), pipe)
