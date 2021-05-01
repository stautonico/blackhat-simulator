from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output
from ..lib.stdlib import setenv, unsetenv, get_env

__COMMAND__ = "export"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.0"


def parse_args(args=[], doc=False):
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("var", nargs="+")
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

        split_args = " ".join(args.var).split("=")

        # The key doesn't need any spaces
        split_args[0] = split_args[0].strip(" ")

        # Remove extra space in front of value
        if split_args[1].startswith(" "):
            split_args[1] = split_args[1][1:]

        if len(split_args) == 1:
            unsetenv(split_args[0])
        else:
            env_value = split_args[1].replace("\"", "")
            env_value = env_value.replace("\'", "")

            if env_value.startswith("$"):
                env_value = get_env(env_value.replace("$", "")) or ""
            else:
                if ":" in env_value:
                    new_env_value = []
                    for val in env_value.split(":"):
                        if val.startswith("$"):
                            val = get_env(val.replace("$", "")) or ""
                        new_env_value.append(val)

                    env_value = ":".join(new_env_value)

            setenv(split_args[0], env_value)

        return output("", pipe)
