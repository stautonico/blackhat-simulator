from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "export"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return computer.run_command("env", [], pipe)

    split_args = " ".join(args).split("=")

    if len(split_args) == 1:
        computer.sessions[-1].env[split_args[0]] = ""
    else:
        env_value = split_args[1].replace("\"", "")
        env_value = env_value.replace("\'", "")

        computer.sessions[-1].env[split_args[0]] = env_value

    return output("", pipe)