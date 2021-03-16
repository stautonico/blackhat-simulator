from ..lib.output import output
from ..helpers import SysCallStatus, SysCallMessages
from ..computer import Computer
from time import sleep

__COMMAND__ = "reboot"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # Only root can reboot
    if computer.get_uid() == 0:
        print(f"Rebooting...")
        sleep(1)
        computer.run_command("clear", [], pipe=True)
        computer.init()
        while len(computer.sessions) != 1:
            computer.run_command("exit", [], pipe=True)

        return output("", pipe)
    else:
        return output(f"{__COMMAND__}: permission denied", pipe, success=False)