from hashlib import md5

from ...computer import Computer
from ...helpers import Result
from ...lib.input import ArgParser
from ...lib.output import output

__COMMAND__ = "john"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.0"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("password", help="The unshadowed file to crack")
    parser.add_argument("--wordlist", help="The wordlist to use when brute-forcing the passwords", required=True)
    parser.add_argument("-o", "--output", help="Output the result to a file")
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


def main(computer: Computer, args: list, pipe: bool) -> Result:
    # TODO: Add ability for john to crack more than just user passwords
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

        find_password_file = computer.fs.find(args.password)
        find_wordlist_file = computer.fs.find(args.wordlist)

        if not find_password_file.success:
            return output(f"{__COMMAND__}: {args.password}: No such file or directory", pipe, success=False)

        if not find_wordlist_file.success:
            return output(f"{__COMMAND__}: {args.wordlist}: No such file or directory", pipe, success=False)

        try_read_password_file = find_password_file.data.read(computer)
        try_read_wordlist_file = find_wordlist_file.data.read(computer)

        if not try_read_password_file.success:
            return output(f"{__COMMAND__}: {args.password}: Permission denied", pipe, success=False)

        if not try_read_wordlist_file.success:
            return output(f"{__COMMAND__}: {args.wordlist}: Permission denied", pipe, success=False)

        password_content = try_read_password_file.data
        wordlist_content = try_read_wordlist_file.data.split("\n")

        user_password_split = [x.split(":") for x in password_content.split("\n") if x != ""]

        clean_user_password = []
        to_crack = {}

        # Now we want to validate the data in each element
        # Each sub-element in the array should have 2 elements
        # The second (index 1) should have a length of exactly 32 (MD5 hash)
        for item in user_password_split:
            if len(item) == 2:
                if len(item[1]) == 32:
                    clean_user_password.append(item)

        for item in clean_user_password:
            if item[1] in to_crack.keys():
                to_crack[item[1]].append(item[0])
            else:
                to_crack[item[1]] = [item[0]]

        if len(clean_user_password) == 0:
            return output(f"{__COMMAND__}: No valid username-password combinations!", pipe, success=False)

        # Used for -o (write to file)
        output_text = ""

        # Loop through all items in the password list and check if the hash matches any of our users
        for password in wordlist_content:
            hashed_password = md5(password.encode()).hexdigest()
            if hashed_password in to_crack.keys():
                for item in to_crack[hashed_password]:
                    response = f"{password}\t({item})"
                    output_text += response + "\n"
                    print(response)

                del to_crack[hashed_password]

            if len(to_crack) == 0:
                break

        if len(to_crack) > 0:
            print(f"{__COMMAND__}: Wordlist exhausted")

        # If we're outputting, we should try to find the file to write to.
        if args.output:
            find_output_file = computer.fs.find(args.output)
            if find_output_file.success:
                write_result = find_output_file.data.write(output_text, computer)
            else:
                # Create the file
                touch_output = computer.run_command("touch", [args.output], pipe)
                if not touch_output.success:
                    return output(f"{__COMMAND__}: cannot open '{args.output}' for writing: Permission denied", pipe,
                                  success=False)
                find_output_file = computer.fs.find(args.output)
                if find_output_file.success:
                    write_result = find_output_file.data.write(output_text, computer)
                else:
                    return output(f"{__COMMAND__}: cannot open '{args.output}' for writing: Permission denied", pipe,
                                  success=False)

            if not write_result.success:
                return output(f"{__COMMAND__}: cannot open '{args.output}' for writing: Permission denied", pipe,
                              success=False)

        return output("", pipe)
