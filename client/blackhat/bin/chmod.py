from ..computer import Computer
from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "chmod"
__VERSION__ = "1.1"


def parse_characters(chars, current_perms):
    split_args = None
    mode = None

    if "+" in chars:
        split_args = chars.split("+")
        mode = "add"
    elif "-" in chars:
        split_args = chars.split("-")
        mode = "remove"

    if split_args:
        if len(split_args) != 2:
            return False
    else:
        return None

    owner, group, public = False, False, False
    read, write, execute = False, False, False
    # Lets figure out who we're modifying
    # If the user arg (split_args[0]) is empty, we can also assume we're modifying everyone
    if len(split_args[0]) == 0:
        owner, group, public = True, True, True
    for user in split_args[0]:
        if user == "a":
            # All
            owner, group, public = True, True, True
            # Don't bother checking the rest because we know that we're doing all of them
            break
        elif user == "u":
            # User/owner
            owner = True
        elif user == "g":
            # Group
            group = True
        elif user == "o":
            # Other/Public
            public = True
        else:
            # Invalid
            return False

    # Now lets see what permissions we're changing
    for perm in split_args[1]:
        if perm == "r":
            read = True
        elif perm == "w":
            write = True
        elif perm == "x":
            execute = True
        else:
            return False

    # FIXME: Holy fuck This needs SERIOUS work
    # DATE: 3/15/2021
    # DATE: 3/19/2021
    # DATE: 4/14/2021
    # Now lets apply the new permissions
    if mode == "remove":
        for mode in ["read", "write", "execute"]:
            # print(f"eval({mode}): {eval(mode)}")
            if eval(mode):
                for perm in ["owner", "group", "public"]:
                    if eval(perm):
                        if perm in current_perms[mode]:
                            # print(f"changing {mode} in {perm}")
                            current_perms[mode].remove(perm)
    else:
        # Add permissions mode
        for mode in ["read", "write", "execute"]:
            if eval(mode):
                for perm in ["owner", "group", "public"]:
                    if eval(perm):
                        if perm not in current_perms[mode]:
                            current_perms[mode].append(perm)

    return True


def main(computer: Computer, args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("umask")
    parser.add_argument("file")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.umask and not args.file:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # Try to find the target file
        find_file_response = computer.fs.find(args.file)

        if not find_file_response.success:
            return output(f"{__COMMAND__}: cannot access '{args.file}': No such file or directory", pipe,
                          success=False)

        file_to_update = find_file_response.data

        # TODO: Make the ability to use octals (chmod 777 file) to change permissions instead of ascii

        # I can't figure out how to pass by value so imma just do this so it prevents the permissions from being changed
        if file_to_update.check_owner(computer):
            new_perms = parse_characters(args.umask, file_to_update.permissions)

            if not new_perms:
                return output(f"{__COMMAND__}: invalid mode: '{args.umask}'", pipe, success=False)

            # TODO: Find a way to move this out of a binary and into the FSBaseObject itself
            file_to_update.handle_event("change_perm")
            return output("", pipe)
        else:
            return output(f"{__COMMAND__}: changing permissions of '{args.file}': Operation not permitted",
                          pipe,
                          success=False)
