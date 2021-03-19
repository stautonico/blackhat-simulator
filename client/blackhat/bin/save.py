import os

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "save"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) > 0:
        output_file = args[0]
    else:
        output_file = "blackhat.save"

    if not output_file.endswith(".save"):
        output_file += ".save"

    # We're going to temporarily disable debug mode (for manual saving)
    prev_debug_mode = os.environ.get("DEBUGMODE", "false")
    os.environ["DEBUGMODE"] = "false"
    save_result = computer.save(output_file)
    # Restore to what it was before after saving
    os.environ["DEBUGMODE"] = prev_debug_mode

    if not save_result:
        return output(f"{__COMMAND__}: Failed to save!", pipe, success=False)

    return output(f"{__COMMAND__}: Successfully saved to {output_file}!", pipe)
