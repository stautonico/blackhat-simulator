from .service import Service
from ..helpers import Result


class SSHServer(Service):
    """
    An example service that's supposed to replicate the functionality of an SSH Server (main method doesn't work like other services)
    """

    def __init__(self, computer):
        super().__init__("SSH", 22, computer)

    def main(self, args: dict) -> Result:
        return Result(success=True, data={"args": args})
