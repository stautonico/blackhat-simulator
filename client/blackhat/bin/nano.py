from os import system, remove
from secrets import token_hex

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "nano"
__VERSION__ = "1.0.0"


# BUG: nano can read files no matter the read permissions
# NOTE: This is only temporary so the user can edit files until the GUI is implemented

def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    exists = False

    if len(args) == 0:
        return output(f"{__COMMAND__}: a filename is required", pipe, success=False)

    find_response = computer.fs.find(args[0])

    if not find_response.success:
        find_response = computer.fs.find("/".join(args[0].split("/")[:-1]))
        if not find_response.success:
            return output(f"{__COMMAND__}: No such file or directory", pipe, success=False)
        else:
            # Create the new file
            create_file_response = computer.run_command("touch", [args[0]], True)
            if not create_file_response.success:
                return output(f"{__COMMAND__}: Unable to create file: {args[0]}", pipe, success=False)
            else:
                file_to_write = computer.fs.find(args[0])["file"]
    else:
        # If this exists, the file already existed, we can read its contents
        # and write it into the physical file
        exists = True
        file_to_write = find_response.data

    if file_to_write.is_directory():
        return output(f"{__COMMAND__}: {args[0]}: Is a directory", pipe, success=False)

    # Create a temporary dir in the real /tmp to write to and read from because im not re-writing nano from scratch
    # for this dumb ass game
    temp_file = token_hex(6)

    try:
        if exists:
            with open(f"/tmp/{temp_file}", "w") as f:
                f.write(file_to_write.content)

        system(f"nano /tmp/{temp_file}")

        with open(f"/tmp/{temp_file}", "r") as f:
            file_content = f.read()

        remove(f"/tmp/{temp_file}")

        write_result = file_to_write.write(computer.users[computer.get_uid()], file_content)

        if not write_result:
            return output(f"{__COMMAND__}: {args[0]}: Permission denied", pipe, success=False)

        return output("", pipe)

    except Exception as e:
        return output(f"{__COMMAND__}: Failed to write file!", pipe, success=False)
