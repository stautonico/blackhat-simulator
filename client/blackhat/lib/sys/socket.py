import ipaddress
from typing import Optional

from client.blackhat.helpers import Result, ResultMessages

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


# Domains
AF_INET = 0

# Socket types
SOCK_STREAM = 0


class SockAddr:
    def __init__(self, family: int, port: int, addr: str):
        self.family = family
        self.port = port
        self.addr = addr


# This is stupid but realistic, so we'll gonna use it
class Socket:
    def __init__(self, domain: int, type: int):
        self.domain = domain
        self.type = type
        self.host = None
        self.port = None


def connect(sockfd: Socket, addr: SockAddr) -> Result:

    # See if we have to resolve a dns record or not
    try:
        is_ipv4 = ipaddress.ip_address(addr.addr)
    except ValueError:
        is_ipv4 = False

    if not is_ipv4:
        resolve_dns_result = computer.parent.parent.services[53].resolve_dns(addr.addr)

        if not resolve_dns_result.success:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        addr.addr = resolve_dns_result.data

    find_client = computer.parent.find_client(addr.addr, port=addr.port)

    if not find_client.success:
        return Result(success=False, message=ResultMessages.NOT_FOUND)

    sockfd.host = addr.addr
    sockfd.port = addr.port

    return Result(success=True)
