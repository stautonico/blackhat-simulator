from ..computer import Computer
from ..helpers import Result, ResultMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "rm"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> Result:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("source")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-r", "-R", "--recursive", action="store_true")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    if args.version:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # Special case for * (all files in current dir)
        to_delete = []

        if args.source == "*":
            for file in getcwd().files:
                to_delete.append(file)
        elif "*" in args.source:
            if args.source[-1] != "*":
                return output(f"{__COMMAND__}: cannot find '{args.source}': No such file or directory", pipe,
                              success=False)
            else:
                # Find the dir without the star
                path_without_star = "/".join(args.source.split("/")[:-1])
                result = computer.fs.find(path_without_star)
                if not result.success:
                    return output(f"{__COMMAND__}: cannot find '{args.source}': No such file or directory", pipe,
                                  success=False)
                else:
                    for file in result.data.files:
                        to_delete.append(f"{path_without_star}/{file}")
        else:
            to_delete.append(args.source)

        for file in to_delete:
            result = computer.fs.find(file)

            if not result.success:
                return output(f"{__COMMAND__}: cannot find '{file}': No such file or directory", pipe, success=False)
            else:
                if result.data.is_directory() and not args.recursive:
                    return output(f"{__COMMAND__}: cannot remove '{file}': Is a directory", pipe, success=False)
                else:
                    response = result.data.delete(computer)

                    if not response.success:
                        if response.message == ResultMessages.NOT_ALLOWED:
                            return output(f"{__COMMAND__}: cannot remove '{file}': Permission denied", pipe,
                                          success=False)
                    else:
                        if args.verbose:
                            print(f"removed '{file}'")

        return output("", pipe)
