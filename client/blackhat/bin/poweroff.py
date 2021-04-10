from time import sleep

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "poweroff"
__DESCRIPTION__ = "power-off or reboot the machine"
__DESCRIPTION_LONG__ = "**poweroff*/, **reboot*/ may be used to power-off or reboot the machine. Both commands take the same options."
__VERSION__ = "1.2"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("-p", "--poweroff", action="store_true",
                        help="Power-off the machine, regardless of which one of the two commands is invoked.")
    parser.add_argument("--reboot", action="store_true",
                        help="Reboot the machine, regardless of which one of the three commands is invoked.")

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


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    args, parser = parse_args(args)

    if parser.error_message:
        return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # TODO: Add ability to power off/reboot external machines via SSH
        # Only root can reboot/power off
        if computer.get_uid() == 0:
            if args.reboot:
                print(f"Rebooting...")
                sleep(1)
                computer.run_command("clear", [], pipe=True)
                computer.init()
                while len(computer.sessions) != 1:
                    computer.run_command("exit", [], pipe=True)

                return output("", pipe)

            exit(0)
        else:
            return output(f"{__COMMAND__}: permission denied", pipe, success=False)
