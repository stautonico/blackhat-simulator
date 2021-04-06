from typing import Union

from ..computer import Computer
from ..fs import File, Directory
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "cp"
__VERSION__ = "1.1"


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
            if not src.check_perm("read", computer).success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer).success:
                    return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_WRITE)
                else:
                    to_write.write(src.content, computer)
                    to_write.owner = computer.get_uid()
                    to_write.group_owner = computer.get_gid()
        else:
            # If we have the parent dir, we need to create a new file
            if not src.check_perm("read", computer).success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer).success:
                    return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_WRITE)
                else:
                    new_filename = new_file_name
                    new_file = File(new_filename, src.content, to_write, computer.get_uid(), computer.get_gid())
                    to_write.add_file(new_file)
                    # We have to do this so the permissions work no matter if we're overwriting or not
                    to_write = new_file

        if preserve_permissions:
            to_write.permissions = src.permissions

        return SysCallStatus(success=True)
    # Handle directory copying
    else:
        # TODO: Refactor this to work in both cases instead of re-writing a ton of code
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
            if not src.check_perm("read", computer):
                return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_READ)
            else:
                if not to_write.check_perm("write", computer).success:
                    return SysCallStatus(success=False, message=SysCallMessages.NOT_ALLOWED_WRITE)
                else:
                    new_dir = Directory(new_file_name, to_write, computer.get_uid(), computer.get_gid())
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
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("-r", dest="recursive", action="store_true")
    parser.add_argument("-p", dest="preserve_permissions", action="store_true")
    parser.add_argument("-v", dest="verbose", action="store_true")
    parser.add_argument("--version", action="store_true", help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.source and not args.destination:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # Try to find the source file/directory
        find_src_result = computer.fs.find(args.source)

        if not find_src_result.success:
            return output(f"{__COMMAND__}: cannot find '{args.source}': No such file or directory", pipe,
                          success=False)
        # The source file exists
        else:
            # Error for trying to copy a directory with the `-r` flag
            if find_src_result.data.is_directory() and not args.recursive:
                return output(f"{__COMMAND__}: -r not specified; omitting directory '{args.source}'", pipe,
                              success=False)
            else:
                # Try to copy the item
                copy_result = copy(computer, find_src_result.data, args.destination, args.preserve_permissions,
                                   args.verbose)

                # Output the proper message
                if not copy_result.success:
                    if copy_result.message == SysCallMessages.NOT_FOUND:
                        return output(f"{__COMMAND__}: cannot find '{args.destination}': No such file or directory",
                                      pipe,
                                      success=False)
                    elif copy_result.message == SysCallMessages.NOT_ALLOWED_READ:
                        return output(f"{__COMMAND__}: cannot open '{args.source}' for reading: Permission denied",
                                      pipe,
                                      success=False)
                    elif copy_result.message == SysCallMessages.NOT_ALLOWED_WRITE:
                        return output(
                            f"{__COMMAND__}: cannot open '{args.destination} for writing: Permission denied", pipe,
                            success=False)
                    elif copy_result.message == SysCallMessages.ALREADY_EXISTS:
                        return output(f"{__COMMAND__}: cannot write '{args.destination}: Directory already exists",
                                      pipe,
                                      success=False)

            return output("", pipe, success=True)
