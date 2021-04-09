from ..computer import Computer
from ..fs import Directory
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "mkdir"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("directories", nargs="+")
    parser.add_argument("-p", dest="create_parents", action="store_true")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.directories:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        for filename in args.directories:
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
                        continue
                    # Success!
                    new_filename = filename.split("/")[-1]
                    dir_to_write_to = result.data
            else:
                if filename not in computer.get_pwd().files:
                    new_filename = filename
                    dir_to_write_to = computer.get_pwd()
                else:
                    continue

            # Make sure that we have write permissions of the dir
            if dir_to_write_to.check_perm("write", computer).success:
                newfile = Directory(new_filename, dir_to_write_to, computer.get_uid(), computer.get_gid())
                dir_to_write_to.add_file(newfile)
                continue
            else:
                continue
    return output("", pipe)
