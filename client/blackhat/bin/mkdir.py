from ..lib.output import output
from ..helpers import SysCallStatus, SysCallMessages
from ..computer import Computer
from ..fs import Directory

__COMMAND__ = "mkdir"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: missing arguments", pipe, success=False)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)


    for filename in args:
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
                    return output(f"{__COMMAND__}: cannot touch '{filename}': No such file or directory", pipe,
                                        success=False)
                # Success!
                new_filename = filename.split("/")[-1]
                dir_to_write_to = result.data
        else:
            if filename not in computer.sessions[-1].current_dir.files:
                new_filename = filename
                dir_to_write_to = computer.sessions[-1].current_dir
            else:
                return output("", pipe)

        # Make sure that we have write permissions of the dir
        if dir_to_write_to.check_perm("write", computer.get_uid() ).success:
            # TODO: CHANGE the 0 to the group id
            newfile = Directory(new_filename, dir_to_write_to, computer.get_uid(), 0)
            dir_to_write_to.add_file(newfile)
            return output("", pipe)
        else:
            return output(f"{__COMMAND__}: cannot touch '{filename}': Permission denied", pipe, success=False)