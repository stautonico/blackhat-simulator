from base64 import b32decode, b32encode
from binascii import Error

from ..computer import Computer
from ..fs import File
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "base32"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (h3xNet coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output("", pipe)

    decode = False

    if "-d" in args:
        decode = True
        args.remove("-d")

    find_file_result = computer.fs.find(args[0])
    if not find_file_result.success:
        if decode:
            try:
                output_text = f"{b32decode(' '.join(args)).decode()}"
            except Error:
                output_text = f"{__COMMAND__}: invalid input"
        else:
            output_text = f"{b32encode(' '.join(args).encode()).decode()}"
    else:
        output_text = ""
        for arg in args:
            find_file_result = computer.fs.find(args[0])
            if not find_file_result.success:
                output_text += f"{__COMMAND__}: {arg}: No such file or directory\n"
            else:
                file: File = find_file_result.data
                if file.is_directory():
                    output_text += f"{__COMMAND__}: {arg}: Is a directory\n"
                else:
                    # We need read perms!
                    if not file.check_perm("read", computer).success:
                        output_text += f"{__COMMAND__}: {arg}: Permission denied\n"
                    else:
                        if decode:
                            try:
                                output_text += f"{b32decode(file.content).decode()}\n"
                            except Error:
                                output_text += f"{__COMMAND__}: {arg}: invalid input\n"
                        else:
                            output_text += f"{b32encode(file.content.encode()).decode()}\n"
        output_text = output_text[:-1]
    return output(output_text, pipe)
