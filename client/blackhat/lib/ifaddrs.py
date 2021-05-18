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


class ifaddrs:
    def __init__(self, ifa_name: str, ifa_addr: str, ifa_netmask: str):
        """
        A 'struct' containing information about a network card
        Args:
            ifa_name (str): The name of the network card
            ifa_addr (str): The current IP address of the card
            ifa_netmask (str): The current netmask of the card
        """
        self.ifa_name = ifa_name
        self.ifa_addr = ifa_addr
        self.ifa_netmask = ifa_netmask


def getifaddrs() -> Result:
    """
    Get info about the current network device

    Returns:
        Result: A `Result` object containing an `ifaddrs` struct with data about the current network device
    """
    return Result(success=True, data=ifaddrs(ifa_name="eth0", ifa_addr=computer.lan, ifa_netmask="255.255.255.0"))
