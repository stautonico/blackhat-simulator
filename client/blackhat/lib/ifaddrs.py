from typing import Optional

from client.blackhat.helpers import Result

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


class ifaddrs:
    def __init__(self, ifa_name: str, ifa_addr: str, ifa_netmask: str):
        self.ifa_name = ifa_name
        self.ifa_addr = ifa_addr
        self.ifa_netmask = ifa_netmask


def getifaddrs() -> Result:
    return Result(success=True, data=ifaddrs(ifa_name="eth0", ifa_addr=computer.lan, ifa_netmask="255.255.255.0"))
