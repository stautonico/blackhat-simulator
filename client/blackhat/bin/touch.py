from ..computer import Computer
from ..fs import File
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "touch"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)

    parser.add_argument("files", nargs="+")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.files:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        output_text = ""

        for filename in args.files:
            new_filename = None
            dir_to_write_to = None

            if "/" in filename:
                # We try to find the entire path at first (we expect this to fail)
                result = computer.fs.find(filename)
                if not result.success:
                    # We want to try one more time, but remove what we expect to be the filename
                    result = computer.fs.find("/".join(filename.split("/")[:-1]))
                    # If this fails, we can assume that the directory the user entered is bad
                    if not result.success:
                        output_text += f"{__COMMAND__}: cannot touch '{filename}': No such file or directory\n"
                    # Success!
                    new_filename = filename.split("/")[-1]
                    dir_to_write_to = result.data
            else:
                if filename not in computer.get_pwd().files:
                    new_filename = filename
                    dir_to_write_to = computer.get_pwd()
                else:
                    return output("", pipe, success=False)

            # Make sure that we have write permissions of the dir
            if dir_to_write_to.check_perm("write", computer).success:
                newfile = File(new_filename, "", dir_to_write_to, computer.get_uid(), computer.get_gid())
                dir_to_write_to.add_file(newfile)
            else:
                output_text += f"{__COMMAND__}: cannot touch '{filename}': Permission denied\n"

        return output(output_text, pipe)
