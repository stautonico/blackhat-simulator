import ipaddress
from typing import Optional

from ..helpers import Result

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


class hostent:
    def __init__(self, h_name: str, h_addr: str):
        """
        An 'struct' object that holds info about a given host
        """
        self.h_name = h_name
        self.h_addr = h_addr


def __str__(self):
    return f"hostent(h_name={self.h_name}, h_addr={self.h_addr})"


def gethostbyname(name: str, dns_server: Optional[str] = None) -> Result:
    """
    Resolve a DNS domain. Use a specific DNS server or use the systems default DNS server(s)
    Args:
        name (str): The domain name to resolve
        dns_server (str, optional): The IP address of the DNS server to use when resolving the domain

    Returns:
        Result: A `Result` object with the success flag set accordingly
    """
    # See if we have to resolve a dns record or not
    try:
        is_ipv4 = ipaddress.ip_address(name)
    except ValueError:
        is_ipv4 = False

    if is_ipv4:
        return Result(success=True, data=hostent(h_name=name, h_addr=name))

    resolve_result = computer.resolve_dns(name, dns_server)

    if not resolve_result.success:
        return Result(success=False, message=resolve_result.message)

    entry = hostent(h_name=name, h_addr=resolve_result.data)
    return Result(success=True, data=entry)
