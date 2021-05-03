import datetime

from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import read

__COMMAND__ = "uptime"
__DESCRIPTION__ = "Tell how long the system has been running."
__DESCRIPTION_LONG__ = "**uptime*/  gives  a  one line display of the following information.  The current time and how long the system has been running."
__VERSION__ = "1.2"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("-p", "--pretty", action="store_true", help="show uptime in pretty format")
    parser.add_argument("-s", "--since", action="store_true", help="system up since, in yyyy-mm-dd HH:MM:SS format")
    parser.add_argument("-V", "--version", action="store_true", help=f"output version information and exit")

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
            return output(f"uptime from blackhat sysutils {__VERSION__}", pipe)

        # TODO: Create special attribute for files in /proc so that they can't be modified
        # For now, just trust that they'll exist
        read_uptime = read("/proc/uptime")

        if not read_uptime.success:
            raise Exception

        total_seconds = int(float(read_uptime.data))

        if args.since:
            return output((datetime.datetime.now() - datetime.timedelta(seconds=total_seconds)).strftime("%Y-%m-%d %H:%M:%S"), pipe)

        seconds = total_seconds % (24 * 3600)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60

        if args.pretty:
            if hours == 0:
                if minutes == 1:
                    output_text = "up %d minute" % minutes
                else:
                    output_text = "up %d minutes" % minutes
            else:
                output_text = "up %d "
                if hours == 1:
                    output_text += "hour, %d "
                else:
                    output_text += "hours, %d "

                if minutes == 1:
                    output_text += "minute"
                else:
                    output_text += "minutes"

                output_text = output_text % (hours, minutes)
            return output(output_text, pipe)

        output_time = "%d:%02d:%02d" % (hours, minutes, seconds)

        return output(f"uptime: {output_time}", pipe)
