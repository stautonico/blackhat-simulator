from types import SimpleNamespace

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "uname"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__, description="Print certain system information.  With no OPTION, same as -s.")

    parser.add_argument("-a", "--all", action="store_true",
                        help="print all information, in the following order, except omit -p and -i if unknown")
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
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

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
            "nodename": computer.hostname,
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
