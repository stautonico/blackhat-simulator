from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "chown"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("owner")
    parser.add_argument("file")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.owner and not args.file:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)


    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        group_owner = None

        if ":" in args.owner:
            params_split = args.owner.split(":")
            owner = params_split[0]
            group_owner = params_split[1]
        else:
            owner = args.owner

        check_user_exists = computer.find_user(username=owner)

        if not check_user_exists.success:
            return output(f"{__COMMAND__}: invalid user: {owner}", pipe, success=False)
        else:
            # Get the user object (because owner is the username (string))
            owner = check_user_exists.data.uid

        # Make sure the group exists (if we're using it)
        if group_owner:
            check_group_exists = computer.find_group(name=group_owner)
            if not check_group_exists.success:
                return output(f"{__COMMAND__}: invalid group: {group_owner}", pipe, success=False)
            else:
                group_owner = check_group_exists.data.gid

        result = computer.fs.find(args.file)

        if result.success:
            # Check if the dir we're trying to change is the root dir (we cant change perm)
            if not result.data.parent:
                return output(f"{__COMMAND__}: Can't change owner of /", pipe, success=False)
            else:
                # Syscall
                update_response = result.data.change_owner(computer, new_user_owner=owner,
                                                           new_group_owner=group_owner)
                if not update_response.success:
                    if update_response.message == SysCallMessages.NOT_ALLOWED:
                        return output(
                            f"{__COMMAND__}: changing ownership of '{args.file}': Operation not permitted",
                            pipe,
                            success=False)
                    else:
                        return output(
                            f"{__COMMAND__}: changing ownership of '{args.file}': Failed to change", pipe,
                            success=False)
        else:
            return output(f"{__COMMAND__}: cannot access '{args.file}': No such file or directory", pipe,
                          success=False)

    return output("", pipe)
