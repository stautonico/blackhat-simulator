from ..computer import Computer
from ..helpers import Result
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "export"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("var", nargs="+")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.var:
            return computer.run_command("env", [], pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        split_args = " ".join(args.var).split("=")

        # The key doesn't need any spaces
        split_args[0] = split_args[0].strip(" ")

        # Remove extra space in front of value
        if split_args[1].startswith(" "):
            split_args[1] = split_args[1][1:]

        if len(split_args) == 1:
            computer.sessions[-1].env[split_args[0]] = ""
        else:
            env_value = split_args[1].replace("\"", "")
            env_value = env_value.replace("\'", "")

            if env_value.startswith("$"):
                env_value = computer.get_env(env_value.replace("$", ""))
                if not env_value:
                    env_value = ""
            else:
                if ":" in env_value:
                    new_env_value = []
                    for val in env_value.split(":"):
                        if val.startswith("$"):
                            val = computer.get_env(val.replace("$", ""))
                            if not val:
                                val = ""
                        new_env_value.append(val)

                    env_value = ":".join(new_env_value)

            computer.sessions[-1].env[split_args[0]] = env_value

        return output("", pipe)
