from typing import Optional

from ...helpers import Result, ResultMessages

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    """
    Store a reference to the games current `Computer` object as a global variable so methods can reference it without
    requiring it as an argument
    
    Args:
        comp (:obj:`Computer`): The games current `Computer` object

    Returns:
        None
    """
    global computer
    computer = comp


# Domains
AF_INET = 0

# Socket types
SOCK_STREAM = 0


class SockAddr:
    def __init__(self, family: int, port: int, addr: str):
        """
        SockAddr struct that contains the address and port of the service to connect to

        Args:
            family (int): The type of socket
            port (int): The port the service is running on
            addr (str): The IP address of the host machine to connect to
        """
        self.family = family
        self.port = port
        self.addr = addr

    def __str__(self):
        return f"SockAddr(family={self.family}, port={self.port}, addr={self.addr})"


# This is stupid but realistic, so we'll gonna use it
class Socket:
    def __init__(self, domain: int, type: int):
        """
        Object representing a network socket

        Args:
            domain (int): The type of communication (ex. IPv4, IPv6, etc)
            type (int): The type of socket (TCP, UDP, etc)
        """
        self.domain = domain
        self.type = type

        self.client = None

        self.metadata = None

    def __str__(self):
        if self.client:
            return f"Socket(domain={self.domain}, type={self.type}, connected={'True' if self.client else 'False'})"


def connect(sockfd: Socket, addr: SockAddr) -> Result:
    """
    Connect a socket to a service using the address and port provided in the `addr` argument.

    Args:
        sockfd (:obj:`Socket`): The `Socket` object used to connect to the service
        addr (:obj:`SockAddr`): The `SockAddr` struct that contains the address and port to connect to

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    find_client = computer.parent.find_client(addr.addr, port=addr.port)

    if not find_client.success:
        return Result(success=False, message=ResultMessages.NOT_FOUND)

    sockfd.client = find_client.data
    sockfd.metadata = find_client.data.get_metadata()

    return Result(success=True)
