from .cp import copy
from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.output import output

__COMMAND__ = "mv"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) < 2:
        return output(f"{__COMMAND__}: missing arguments", pipe, success=False)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    recursive = False
    preserve_permissions = False
    verbose = False

    if "-r" in args:
        recursive = True
        args.remove("-r")

    if "-p" in args:
        preserve_permissions = True
        args.remove("-p")

    if "-v" in args:
        verbose = True
        args.remove("-v")

    src = args[0]
    dst = args[1]

    src_result = computer.fs.find(src)

    if not src_result.success:
        return output(f"{__COMMAND__}: cannot find '{src}': No such file or directory", pipe, success=False)
    else:
        if src_result.data.is_directory() and not recursive:
            return output(f"{__COMMAND__}: -r not specified; omitting directory '{src}'", pipe, success=False)
        else:
            # Make sure we have proper permissions before copying
            if src_result.data.check_perm("read", computer.users[computer.get_uid()] ).success and src_result.data.check_perm("write",
                                                                                                             computer.get_uid()).success:
                copy_result = copy(computer, src_result.data, dst, preserve_permissions, verbose)

                if not copy_result.success:
                    if copy_result.message == SysCallMessages.NOT_FOUND:
                        return output(f"{__COMMAND__}: cannot find '{dst}': No such file or directory", pipe,
                                      success=False)
                    elif copy_result.message == SysCallMessages.GENERIC:
                        return output(f"{__COMMAND__}: invalid destination '{dst}'", pipe, success=False)
                    elif copy_result.message == SysCallMessages.NOT_ALLOWED_READ:
                        return output(f"{__COMMAND__}: cannot open '{src}' for reading: Permission denied", pipe,
                                      success=False)
                    elif copy_result.message == SysCallMessages.NOT_ALLOWED_WRITE:
                        return output(f"{__COMMAND__}: cannot open '{dst} for writing: Permission denied", pipe,
                                      success=False)
                    elif copy_result.message == SysCallMessages.ALREADY_EXISTS:
                        return output(f"{__COMMAND__}: cannot write '{dst}: Directory already exists", pipe,
                                      success=False)
                else:
                    computer.run_command("rm", [src, "-r"], pipe)
                    if verbose:
                        print(f"{src} -> {dst}")
                    return output("", pipe)
            else:
                return output(f"{__COMMAND__}: cannot open '{src}': Permission denied", pipe, success=False)
