import ipaddress
from random import randint
from time import sleep

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "ping"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("host")
    parser.add_argument("--version", "-V", "-v", action="store_true",
                        help=f"Print the binaries' version number and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    if args.version:
        return output(f"ping from blackhat netutils 1.1", pipe)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # See if we have to resolve a dns record or not
        try:
            is_ipv4 = ipaddress.ip_address(args.host)
        except ValueError:
            is_ipv4 = False

        if not is_ipv4:
            # Resolve the DNS record
            dns_result = computer.parent.resolve_dns(args.host)
            if not dns_result.success:
                # We couldn't resolve the DNS address, show failure message
                return output(f"{__COMMAND__}: {args.host}: Name or service not known", pipe, success=False)
            else:
                to_ping = dns_result.data
        else:
            to_ping = args.host

        # Try to find the given client
        find_client = computer.parent.find_client(to_ping)

        print(f"PING {args.host} ({to_ping}) 56(84) bytes of data.")

        if not find_client.success:
            # Pretend to connect to the host, even tho we already know its dead (for realism)
            sleep(randint(1, 3))
            return output(f"From {to_ping} icmp_seq=1 Destination Host Unreachable", pipe, success=False)
        else:
            return output(
                f"64 bytes from {args.host} ({to_ping}): icmp_seq=1 ttl=116 time={randint(5, 15)}.{randint(0, 9)} ms",
                pipe)
