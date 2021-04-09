from ...computer import Computer
from ...helpers import SysCallStatus
from ...lib.input import ArgParser
from ...lib.output import output

__COMMAND__ = "dig"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("domains", nargs="+")
    parser.add_argument("--version", "-v", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"DiG (blackhat netutils) {__VERSION__}", pipe)

        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        output_text = ""

        # Find the longest domain name (for formatting)
        longest_domain = len(max(args.domains, key=len))

        for domain in args.domains:
            result = computer.parent.resolve_dns(domain)

            if len(domain) == longest_domain:
                output_text += f"{domain}   A  "
            else:
                # Space difference allows the "A  <IP_ADDRESS" to be aligned nicely
                space_difference = longest_domain - len(domain) + 3
                output_text += f"{domain}{' ' * space_difference}A  "

            if not result.success:
                output_text += f"  \n"
            else:
                output_text += f"  {result.data}\n"

        return output(output_text, pipe)
