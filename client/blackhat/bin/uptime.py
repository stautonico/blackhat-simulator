from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output
from time import perf_counter

__COMMAND__ = "uptime"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    now = perf_counter()
    total_seconds = now - computer.boot_time

    seconds = total_seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    output_time = "%d:%02d:%02d" % (hour, minutes, seconds)

    return output(f"uptime: {output_time}", pipe)