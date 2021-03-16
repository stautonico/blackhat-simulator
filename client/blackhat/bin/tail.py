from ..computer import Computer
from ..helpers import SysCallMessages, SysCallStatus
from ..lib.output import output

__COMMAND__ = "head"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: a file argument is required", pipe, success=False,
                      success_message=SysCallMessages.MISSING_ARGUMENT)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    output_text = ""

    for file in args:
        print(f"Handling {file}")
        to_read_result = computer.fs.find(file)

        if not to_read_result.success:
            if to_read_result.message == SysCallMessages.NOT_FOUND:
                output_text += f"{__COMMAND__}: {file}: No such file or directory\n"
            else:
                output_text += f"{__COMMAND__}: Failed to read file\n"

        else:
            to_read = to_read_result.data

            if to_read.is_directory():
                output_text += f"{__COMMAND__}: {file}: Is a directory\n"
            else:
                # Permission checking
                read_response = to_read.read(computer.users[computer.get_uid()])

                if read_response.success:
                    if read_response.data:
                        # Make sure they're are no extra \n at the end
                        if read_response.data.endswith("\n"):
                            read_response.data = read_response.data[:-1]

                        data = read_response.data.split("\n")
                        data = "\n".join(data[-10:])
                        output_text += data
                else:
                    if read_response.message == SysCallMessages.NOT_ALLOWED:
                        output_text += f"{__COMMAND__}: {to_read.name}: Permission denied\n"

    return output(output_text, pipe)
