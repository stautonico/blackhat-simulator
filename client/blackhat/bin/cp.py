from typing import Union

from ..computer import Computer
from ..fs import File, Directory
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.output import output

__COMMAND__ = "cp"
__VERSION__ = "1.0.0"


# TODO: This is old code from the original demo, this will be re-written soon

def copy(computer: Computer, src: Union[File, Directory], dst_path: str, preserve_permissions: bool,
         verbose: bool) -> SysCallStatus:
    # Handle file copying
    if src.is_file():
        # If the path is in the local dir
        if "/" not in dst_path:
            dst_path = "./" + dst_path

        try_find_dst = computer.fs.find(dst_path)

        # If the dst file doesn't exist, we can try to create a new item in the parent folder
        if not try_find_dst.success:
            # Try to find the destination file parent folder
            try_find_dst = computer.fs.find("/".join(dst_path.split("/")[:-1]))
            if not try_find_dst.success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        to_write: Union[Directory, File] = try_find_dst.data

        # If we found the parent folder, set the filename to the parent folder
        if dst_path.split("/")[-1] != to_write.name:
            new_file_name = dst_path.split("/")[-1]
        else:
            new_file_name = src.name

        if to_write.is_file():
            # If its a file, we're overwriting
            # Check the permissions (write to `copy_to_dir + file` and read from `self`)
            # Check read first (split for error messages)
            if not src.check_perm("read", computer.get_uid() ).success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer.get_uid() ).success:
                    return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_WRITE)
                else:
                    to_write.write(computer.get_uid(), src.content)
                    to_write.owner = computer.get_uid()
                    # TODO: Update the file's group owner
        else:
            # If we have the parent dir, we need to create a new file
            if not src.check_perm("read", computer.get_uid() ).success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer.get_uid() ).success:
                    return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_WRITE)
                else:
                    new_filename = new_file_name
                    # TODO: Replace 0 with group owner
                    new_file = File(new_filename, src.content, to_write, computer.get_uid(), 0)
                    to_write.add_file(new_file)
                    # We have to do this so the permissions work no matter if we're overwriting or not
                    to_write = new_file

        if preserve_permissions:
            to_write.permissions = src.permissions

        return SysCallStatus(success=True)
    # Handle directory copying
    else:
        # TODO: Refractor this to work in both cases instead of re-writing a ton of code
        # If the path is in the local dir
        if "/" not in dst_path:
            dst_path = "./" + dst_path

        try_find_dst = computer.fs.find(dst_path)

        # If the dst file doesn't exist, we can try to create a new item in the parent folder
        if not try_find_dst.success:
            # Try to find the destination file parent folder
            try_find_dst = computer.fs.find("/".join(dst_path.split("/")[:-1]))
            if not try_find_dst.success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        to_write: Union[Directory, File] = try_find_dst.data

        # If we found the parent folder, set the filename to the parent folder
        if dst_path.split("/")[-1] != to_write.name:
            new_file_name = dst_path.split("/")[-1]
        else:
            new_file_name = src.name

        if new_file_name not in to_write.files:
            if not src.check_perm("read", computer.get_uid() ):
                return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer.get_uid() ).success:
                    return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_WRITE)
                else:
                    # TODO: Handle group owners
                    new_dir = Directory(new_file_name, to_write, computer.get_uid(), 0)
                    to_write.add_file(new_dir)
                    # Set a temporary write permission no matter what the new dir's permissions were so we can add its children
                    new_dir.permissions["write"] = ["owner"]
                    # Go through all the source's files and copy them into the new dir
                    for file in src.files.values():
                        response = copy(computer, file, new_dir.pwd(), preserve_permissions, verbose)

                        if not response.success:
                            if response.message == SysCallMessages.NOT_ALLOWED_READ:
                                print(f"{__COMMAND__}: cannot open '{file.pwd()}' for reading: Permission denied")
                            elif response.message == SysCallMessages.NOT_ALLOWED_WRITE:
                                print(f"{__COMMAND__}: cannot open '{file.pwd()}' for writing: Permission denied")
        else:
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

        if preserve_permissions:
            new_dir.permissions = src.permissions

        return SysCallStatus(success=True)


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

    # Try to find the source file/directory
    find_src_result = computer.fs.find(src)

    if not find_src_result.success:
        return output(f"{__COMMAND__}: cannot find '{src}': No such file or directory", pipe, success=False)
    # The source file exists
    else:
        # Error for trying to copy a directory with the `-r` flag
        if find_src_result.data.is_directory() and not recursive:
            return output(f"{__COMMAND__}: -r not specified; omitting directory '{src}'", pipe, success=False)
        else:
            # Try to copy the item
            copy_result = copy(computer, find_src_result.data, dst, preserve_permissions, verbose)

            # Output the proper message
            if not copy_result.success:
                if copy_result.message == SysCallMessages.NOT_FOUND:
                    return output(f"{__COMMAND__}: cannot find '{dst}': No such file or directory", pipe,
                                  success=False)
                elif copy_result.message == SysCallMessages.NOT_ALLOWED_READ:
                    return output(f"{__COMMAND__}: cannot open '{src}' for reading: Permission denied", pipe,
                                  success=False)
                elif copy_result.message == SysCallMessages.NOT_ALLOWED_WRITE:
                    return output(f"{__COMMAND__}: cannot open '{dst} for writing: Permission denied", pipe,
                                  success=False)
                elif copy_result.message == SysCallMessages.ALREADY_EXISTS:
                    return output(f"{__COMMAND__}: cannot write '{dst}: Directory already exists", pipe,
                                  success=False)

    return output("", pipe, success=True)
