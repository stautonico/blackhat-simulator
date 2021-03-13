from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "commands"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    output_text = ""

    bin_dir_result = computer.fs.find("/bin")

    if bin_dir_result.success:
        for command in list(bin_dir_result.data.files.keys()):
            output_text += f"{command} "

    return output(output_text, pipe)
