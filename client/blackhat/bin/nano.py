from os import system, remove
from secrets import token_hex

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "nano"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("source")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    if args.version:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        find_response = computer.fs.find(args.source)

        if not find_response.success:
            find_response = computer.fs.find("/".join(args.source.split("/")[:-1]))
            if not find_response.success:
                return output(f"{__COMMAND__}: No such file or directory", pipe, success=False)
            else:
                # Create the new file
                create_file_response = computer.run_command("touch", [args.source], True)
                if not create_file_response.success:
                    return output(f"{__COMMAND__}: Unable to create file: {args.source}", pipe, success=False)
                else:
                    file_to_write = computer.fs.find(args.source).data
        else:
            # If this exists, the file already existed, we can read its contents
            # and write it into the physical file
            exists = True
            file_to_write = find_response.data

        if file_to_write.is_directory():
            return output(f"{__COMMAND__}: {args.source}: Is a directory", pipe, success=False)

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

            write_result = file_to_write.write(file_content, computer)

            if not write_result:
                return output(f"{__COMMAND__}: {args.source}: Permission denied", pipe, success=False)

            return output("", pipe)

        except Exception as e:
            return output(f"{__COMMAND__}: Failed to write file!", pipe, success=False)
