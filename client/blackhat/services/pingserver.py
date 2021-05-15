from .service import Service
from ..helpers import Result


class PingServer(Service):
    """
    A "Server" that all machines have to accept pings
    """

    def __init__(self, computer):
        super().__init__("Ping", 0, computer)

    def main(self, args: dict) -> Result:
        return Result(success=True)
