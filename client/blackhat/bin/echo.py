from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "echo"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output("", pipe)

    # If the output starts with $, read from env vars
    if args[0].startswith("$"):
        env_var = computer.sessions[-1].env.get(args[0].replace("$", ""))
        return output(env_var or "", pipe)

    return output(" ".join(args), pipe)
