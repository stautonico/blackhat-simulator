from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.unistd import getuid, get_user, get_group, get_user_primary_group, get_user_groups

__COMMAND__ = "id"
__DESCRIPTION__ = "print real and effective user and group IDs"
__DESCRIPTION_LONG__ = "Print user and group information for each specified USER, or (when USER omitted) for the current user."
__VERSION__ = "1.2"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("user", nargs="?")
    parser.add_argument("-g", "--group", action="store_true", help="print only the effective group ID")
    parser.add_argument("-G", "--groups", action="store_true", help="print all group IDs")
    parser.add_argument("-n", "--name", action="store_true", help="print a name instead of a number, for -u")
    parser.add_argument("-u", "--user", dest="user_only", action="store_true", help="print only the effective user ID")
    parser.add_argument("-z", "--zero", action="store_true",
                        help="delimit entries with NUL characters, not whitespace;\n\n\t\tnot permitted in default format")
    parser.add_argument("--version", action="store_true", help=f"print program version")

    args = parser.parse_args(args)

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION_LONG__}\n\n"

    for item in arg_helps:
        # Its a positional argument
        if len(item.option_strings) == 0:
            # If the argument is optional:
            if item.nargs == "?":
                SYNOPSIS += f"[{item.dest.upper()}] "
            elif item.nargs == "+":
                SYNOPSIS += f"[{item.dest.upper()}]... "
            else:
                SYNOPSIS += f"{item.dest.upper()} "
        else:
            # Boolean flag
            if item.nargs == 0:
                if len(item.option_strings) == 1:
                    DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/\t{item.help}\n\n"
                else:
                    DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/\n\t\t{item.help}\n\n"
            elif item.nargs == "+":
                DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/=[{item.dest.upper()}]...\n\t\t{item.help}\n\n"
            else:
                DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/={item.dest.upper()}\n\t\t{item.help}\n\n"

    if doc:
        return f"{NAME}\n\n{SYNOPSIS}\n\n{DESCRIPTION}\n\n"
    else:
        return args, parser


def main(args: list, pipe: bool) -> Result:
    args, parser = parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if args.user:
            # Check if a UID was entered
            try:
                uid = int(args.user)
                user_to_lookup_result = get_user(uid=uid)
            except ValueError:
                # That means we entered a username
                user_to_lookup_result = get_user(username=args.user)
        else:
            user_to_lookup_result = get_user(uid=getuid())

        if not user_to_lookup_result.success:
            return output(f"{__COMMAND__}: '{args.user}': no such user", pipe, success=False)
        else:
            user = user_to_lookup_result.data
            uid = user.uid
            primary_group_gid = get_user_primary_group(uid).data[0]
            secondary_groups_gids = get_user_groups(uid)
            secondary_groups_gids = secondary_groups_gids.data if secondary_groups_gids.success else []
            secondary_groups_gids.remove(primary_group_gid)

            primary_group_name = get_group(gid=primary_group_gid)

            if not primary_group_name.success:
                primary_group_name = "?"
            else:
                primary_group_name = primary_group_name.data.name

            secondary_group_names = []

            for item in secondary_groups_gids:
                find_secondary_group = get_group(gid=item)
                if not find_secondary_group.success:
                    secondary_group_names.append("?")
                else:
                    secondary_group_names.append(find_secondary_group.data.name)

            if args.group:
                return output(f"{primary_group_gid}", pipe)

            if args.groups:
                if args.zero:
                    return output(f"{''.join(str(x) for x in [primary_group_gid] + secondary_groups_gids)}", pipe)
                return output(f"{' '.join(str(x) for x in [primary_group_gid] + secondary_groups_gids)}", pipe)

            if args.name:
                return output(user.username, pipe)

            if args.user_only:
                return output(f"{uid}", pipe)

            if args.zero:
                return output(f"{__COMMAND__}: option --zero not permitted in default format", pipe, success=False)

            output_text = f"uid={uid}({user.username}) gid={primary_group_gid}({primary_group_name}) "

            if len(secondary_groups_gids) > 0:
                output_text += "groups="

            for group in secondary_groups_gids:
                group_lookup = get_group(gid=group)
                if group_lookup.success:
                    output_text += f"{group}({group_lookup.data.name}),"
                else:
                    output_text += f"{group}(?),"

            if output_text.endswith(","):
                output_text = output_text[:-1]

            return output(output_text, pipe)
