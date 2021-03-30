from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "echo"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output("", pipe)

    clean_args = []

    # If the output starts with $, read from env vars
    for arg in args:
        if arg.startswith("$"):
            env_var = computer.get_env(arg.replace("$", ""))
            if env_var:
                clean_args.append(env_var)
        else:
            clean_args.append(arg)

    return output(" ".join(clean_args), pipe)
