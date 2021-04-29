import ipaddress

from tabulate import tabulate

from ...computer import Computer
from ...helpers import Result
from ...lib.input import ArgParser
from ...lib.output import output

__COMMAND__ = "nmap"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> Result:
    """
    nmap - Network exploration tool and security / port scanner

    # TODO: Complete this manpage
    """
    # TODO: Add some of the flags that nmap has

    parser = ArgParser(prog=__COMMAND__)

    parser.add_argument("--version", action="store_true", help=f"output version information and exit")
    parser.add_argument("host")

    args = parser.parse_args(args)

    if parser.error_message:
        # `host` argument is required unless we have --version
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.host and not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    else:
        # If we specific -h/--help, args will be empty, so exit gracefully
        if not args:
            return output(f"", pipe)
        else:
            # Lets try to find the computer by address
            find_computer_result = computer.parent.find_client(args.host)

            if find_computer_result.success:
                found_comp = find_computer_result.data
                # Now, lets generate a table for outputting
                # Table format is [[<PORT>/tcp, "open", <SERVICE_NAME>]]
                headers = ["PORT", "STATE", "SERVICE"]
                table = []
                # Sort the results by port number (asc)
                for key, value in sorted(found_comp.port_forwarding.items(), key=lambda item: int(item[0])):
                    table.append([f"{key}/tcp", "open", value.services[key].name])

                try:
                    is_ipv4 = ipaddress.ip_address(args.host)
                except ValueError:
                    is_ipv4 = False
                    # Try to resolve the domain to get the ip manually
                    resolve_host = computer.parent.resolve_dns(args.host)
                    if resolve_host.success:
                        domain_ip_address = resolve_host.data
                    else:
                        domain_ip_address = "?"

                # Initial message is different depending on if we passed an ip address or domain name
                if is_ipv4:
                    output_text = f"Nmap scan report for {args.host}"
                else:
                    output_text = f"Nmap scan report for {args.host} ({domain_ip_address})"

                output_text += "\n" + tabulate(table, headers=headers, tablefmt="plain")

                return output(output_text, pipe)
