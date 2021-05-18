from types import SimpleNamespace

from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import gethostname

__COMMAND__ = "uname"
__DESCRIPTION__ = "print system information"
__DESCRIPTION_LONG__ = "Print certain system information.  With no OPTION, same as -s."
__VERSION__ = "1.2"

def parse_args(args=[], doc=False):
    """
    Handle parsing of arguments and flags. Generates docs using help from `ArgParser`

    Args:
        args (list): argv passed to the binary
        doc (bool): If the function should generate and return manpage

    Returns:
        Processed args and a copy of the `ArgParser` object if not `doc` else a `string` containing the generated manpage
    """
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("-a", "--all", action="store_true",
                        help="print all information, in the following order, except omit -p and -i if unknown:")
    parser.add_argument("-s", "--kernel-name", dest="kernel_name", action="store_true", help="print the kernel name")
    parser.add_argument("-n", "--nodename", action="store_true", help="print the network node hostname")
    parser.add_argument("-r", "--kernel-release", dest="kernel_release", action="store_true",
                        help="print the kernel release")
    parser.add_argument("-v", "--kernel-version", dest="kernel_version", action="store_true",
                        help="print the kernel version")
    parser.add_argument("-m", "--machine", action="store_true", help="print the machine hardware name")
    parser.add_argument("-p", "--processor", action="store_true", help="print the processor type (non-portable)")
    parser.add_argument("-i", "--hardware-platform", dest="hardware_platform", action="store_true",
                        help="print the hardware platform (non-portable)")
    parser.add_argument("-o", "--operating-system", dest="operating_system", action="store_true",
                        help="print the operating system")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION_LONG__}\n\n"

    for item in arg_helps:
        # Its a positional argument
        if len(item.option_strings) == 0:
            # If the argument is optional:
            if item.nargs == "?":
                SYNOPSIS += f"[{item.dest.upper()}] "
            elif item.nargs == "+":
                SYNOPSIS += f"[{item.dest.upper()}]... "
            else:
                SYNOPSIS += f"{item.dest.upper()} "
        else:
            # Boolean flag
            if item.nargs == 0:
                if len(item.option_strings) == 1:
                    DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/\t{item.help}\n\n"
                else:
                    DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/\n\t\t{item.help}\n\n"
            elif item.nargs == "+":
                DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/=[{item.dest.upper()}]...\n\t\t{item.help}\n\n"
            else:
                DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/={item.dest.upper()}\n\t\t{item.help}\n\n"

    if doc:
        return f"{NAME}\n\n{SYNOPSIS}\n\n{DESCRIPTION}\n\n"
    else:
        return args, parser

def main(args: list, pipe: bool) -> Result:
    args, parser = parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:

        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        uname = SimpleNamespace(**{
            "kernel_name": "Linux",
            "nodename": gethostname(),
            "kernel_release": "1.1",
            "kernel_version": "v1",
            "machine": "x86_64",
            "processor": "unknown",
            "hardware_platform": "unknown",
            "operating_system": "Blackhat/Linux"
        })

        if not any(vars(args).values()):
            return output(uname.kernel_name, pipe)

        if args.all:
            return output(
                f"{uname.kernel_name} {uname.nodename} {uname.kernel_release} {uname.kernel_version} {uname.machine} {uname.operating_system}",
                pipe)

        output_text = ""

        # HEYYYY no need for a bunch of manual if statements!
        for key, value in vars(args).items():
            if value:
                output_text += vars(uname)[key] + " "

        return output(output_text, pipe)
