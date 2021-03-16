import ipaddress
from random import randint
from time import sleep

from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "ping"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: an address is required", pipe)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    # See if we have to resolve a dns record or not
    try:
        is_ipv4 = ipaddress.ip_address(args[0])
    except ValueError:
        is_ipv4 = False

    if not is_ipv4:
        # Resolve the DNS record
        dns_result = computer.parent.resolve_dns(args[0])
        if not dns_result.success:
            # We couldn't resolve the DNS address, show failure message
            return output(f"{__COMMAND__}: {args[0]}: Name or service not known", pipe, success=False)
        else:
            to_ping = dns_result.data
    else:
        to_ping = args[0]

    # Try to find the given client
    find_client = computer.parent.find_client(to_ping)

    print(f"PING {args[0]} ({to_ping}) 56(84) bytes of data.")

    if not find_client.success:
        # Pretend to connect to the host, even tho we already know its dead (for realism)
        sleep(randint(1, 3))
        return output(f"From {to_ping} icmp_seq=1 Destination Host Unreachable", pipe, success=False)
    else:
        return output(
            f"64 bytes from {args[0]} ({to_ping}): icmp_seq=1 ttl=116 time={randint(5, 15)}.{randint(0, 9)} ms", pipe)
