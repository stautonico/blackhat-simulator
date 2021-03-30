from .service import Service
from ..helpers import SysCallStatus


class SSHServer(Service):
    """
    An example service that's supposed to replicate the functionality of an SSH Server (main method doesn't work like other services)
    """

    def __init__(self):
        super().__init__("SSH", 22)

    def main(self, args: dict) -> SysCallStatus:
        return SysCallStatus(success=True, data={"args": args})
