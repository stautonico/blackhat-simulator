from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "dig"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output(f"{__COMMAND__}: A domain name is required", pipe, success=False)

    domain_name = args[0]

    result = computer.parent.resolve_dns(domain_name)

    if not result.success:
        result.data = ""

    return output(f"{domain_name}   A  {result.data}", pipe)
