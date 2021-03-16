from .service import Service
from ..helpers import SysCallStatus


class WebServer(Service):
    """
    An example service that's supposed to replicate the functionality of a webserver
    As of now (just for example purposes) it just echos args that is sent to it.
    """

    def __init__(self):
        super().__init__("WebServer", 80)

    def main(self, args: dict) -> SysCallStatus:
        return SysCallStatus(success=True, data={"args": args})
