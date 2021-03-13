import datetime
from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "date"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)


    local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    time_first = datetime.datetime.now().strftime('%a %b %d %I:%M:%S %p')
    time_second = datetime.datetime.now().strftime('%Y')

    return output(f"{time_first} {local_timezone} {time_second}", pipe)
