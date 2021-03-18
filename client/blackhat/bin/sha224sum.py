from hashlib import sha224

from ..computer import Computer
from ..fs import File
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "sha224sum"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    find_file_result = computer.fs.find(args[0])
    if not find_file_result.success:
        output_text = f"{sha224(' '.join(args).encode()).hexdigest()}  -"
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
                    if not file.check_perm("read", computer.get_uid() ).success:
                        output_text += f"{__COMMAND__}: {arg}: Permission denied\n"
                    else:
                        hash = sha224(file.content.encode()).hexdigest()
                        output_text += f"{hash}  {arg}\n"
        output_text = output_text[:-1]
    return output(output_text, pipe)
