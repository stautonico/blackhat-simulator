from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.output import output

__COMMAND__ = "rm"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: missing arguments", pipe, success=False)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    recursive = False
    verbose = False

    if "-r" in args:
        recursive = True
        args.remove("-r")

    if "-v" in args:
        verbose = True
        args.remove("-v")

    src = args[0]

    # Special case for * (all files in current dir)

    to_delete = []

    if src == "*":
        for file in computer.get_pwd().files:
            to_delete.append(file)
    elif "*" in src:
        if src[-1] != "*":
            return output(f"{__COMMAND__}: cannot find '{src}': No such file or directory", pipe, success=False)
        else:
            # Find the dir without the star
            path_without_star = "/".join(src.split("/")[:-1])
            result = computer.fs.find(path_without_star)
            if not result.success:
                return output(f"{__COMMAND__}: cannot find '{src}': No such file or directory", pipe,
                              success=False)
            else:
                for file in result.data.files:
                    to_delete.append(f"{path_without_star}/{file}")
    else:
        to_delete.append(src)

    for file in to_delete:
        result = computer.fs.find(file)

        if not result.success:
            return output(f"{__COMMAND__}: cannot find '{file}': No such file or directory", pipe, success=False)
        else:
            if result.data.is_directory() and not recursive:
                return output(f"{__COMMAND__}: cannot remove '{file}': Is a directory", pipe, success=False)
            else:
                response = result.data.delete(computer.get_uid())

                if not response.success:
                    if response.message == SysCallMessages.NOT_ALLOWED:
                        return output(f"{__COMMAND__}: cannot remove '{file}': Permission denied", pipe,
                                      success=False)
                else:
                    if verbose:
                        print(f"removed '{file}'")

    return output("", pipe)
