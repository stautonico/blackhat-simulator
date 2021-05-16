import ipaddress
from typing import Optional

from client.blackhat.helpers import Result

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


class hostent:
    def __init__(self, h_name: str, h_addr: str):
        self.h_name = h_name
        self.h_addr = h_addr

    def __str__(self):
        return f"hostent(h_name={self.h_name}, h_addr={self.h_addr})"


def gethostbyname(name: str, dns_server: Optional[str] = None) -> Result:
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
