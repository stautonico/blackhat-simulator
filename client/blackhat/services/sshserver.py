from .service import Service
from ..helpers import Result


class SSHServer(Service):
    def __init__(self, computer):
        """
        An example service that's supposed to replicate the functionality of an SSH Server (main method doesn't work like other services)
        """
        super().__init__("SSH", 22, computer)

    def main(self, args: dict) -> Result:
        """
        Function that runs when the service is 'connected to'

        Args:
            args (dict): A dict of arguments that is given to the service to process

        Returns:
            Result: A `Result` object containing the success status and resulting data of the service
        """
        return Result(success=True, data={"args": args})
