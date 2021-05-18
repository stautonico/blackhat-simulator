from .service import Service
from ..helpers import Result


class PingServer(Service):
    def __init__(self, computer):
        """
        A "Server" that all machines have to accept pings
        """
        super().__init__("Ping", 0, computer)

    def main(self, args: dict) -> Result:
        """
        Function that runs when the service is 'connected to'

        Args:
            args (dict): A dict of arguments that is given to the service to process

        Returns:
            Result: A `Result` object containing the success status and resulting data of the service
        """
        return Result(success=True)
