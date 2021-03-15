from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.output import output

__COMMAND__ = "rmdir"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: missing arguments", pipe, success=False)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    verbose = False

    if "-v" in args:
        verbose = True
        args.remove("-v")

    src = args[0]

    result = computer.fs.find(src)

    if not result.success:
        return output(f"{__COMMAND__}: cannot find '{src}': No such file or directory", pipe, success=False)
    else:
        if result.data.is_file():
            return output(f"{__COMMAND__}: failed to remove '{src}': Not a directory", pipe, success=False)
        else:
            # rmdir only removes empty dirs
            if len(result.data.files) > 0:
                return output(f"{__COMMAND__}: failed to remove '{src}': Directory not empty", pipe,
                              success=False)
            else:
                response = result.data.delete(computer.get_uid())

                if not response.success:
                    if response.message == SysCallMessages.NOT_ALLOWED:
                        return output(f"{__COMMAND__}: cannot remove '{src}': Permission denied", pipe,
                                      success=False)

    return output(f"removed '{src}'", pipe)
