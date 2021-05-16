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

    def __str__(self):
        return f"SockAddr(family={self.family}, port={self.port}, addr={self.addr})"


# This is stupid but realistic, so we'll gonna use it
class Socket:
    def __init__(self, domain: int, type: int):
        self.domain = domain
        self.type = type

        self.client = None

    def __str__(self):
        if self.client:
            return f"Socket(domain={self.domain}, type={self.type}, connected={'True' if self.client else 'False'})"


def connect(sockfd: Socket, addr: SockAddr) -> Result:
    find_client = computer.parent.find_client(addr.addr, port=addr.port)

    if not find_client.success:
        return Result(success=False, message=ResultMessages.NOT_FOUND)

    sockfd.client = find_client.data

    return Result(success=True)
