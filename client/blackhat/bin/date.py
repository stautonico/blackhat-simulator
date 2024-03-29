__package__ = "blackhat.bin"

from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output

import datetime

__COMMAND__ = "date"
__VERSION__ = "1.1"


def main(args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

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

        local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        time_first = datetime.datetime.now().strftime('%a %b %d %I:%M:%S %p')
        time_second = datetime.datetime.now().strftime('%Y')

        return output(f"{time_first} {local_timezone} {time_second}", pipe)
