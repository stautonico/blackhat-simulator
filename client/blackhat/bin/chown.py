from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.output import output

__COMMAND__ = "chown"
__VERSION__ = "1.0.0"


# TODO: Support group owner changing

def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    # args[0] = new owner
    # args[1] = file to change owner of
    if len(args) < 2:
        return output(f"{__COMMAND__}: missing arguments", pipe, success=False)
    else:

        if "--version" in args:
            return output(f"{__COMMAND__} (h3xNet coreutils) {__VERSION__}", pipe)

        owner = args[0]
        file_to_change = args[1]

        check_user_exists = computer.find_user(username=owner)

        if not check_user_exists.success:
            return output(f"{__COMMAND__}: invalid user: {owner}", pipe, success=False)
        else:
            # Get the user object (because owner is the username (string))
            owner = check_user_exists.data.uid

        result = computer.fs.find(file_to_change)

        if result.success:
            # Check if the dir we're trying to change is the root dir (we cant change perm)
            if not result.data.parent:
                return output(f"{__COMMAND__}: Can't change owner of /", pipe, success=False)
            else:
                # Syscall
                update_response = result.data.change_owner(computer.get_uid(), owner)
                if not update_response.success:
                    if update_response.message == SysCallMessages.NOT_ALLOWED:
                        return output(
                            f"{__COMMAND__}: changing ownership of '{file_to_change}': Operation not permitted", pipe,
                            success=False)
        else:
            return output(f"{__COMMAND__}: cannot access '{file_to_change}': No such file or directory", pipe,
                          success=False)

    return output("", pipe)
