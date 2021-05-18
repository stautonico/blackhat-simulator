from .service import Service
from ..helpers import Result


class WebServer(Service):
    def __init__(self, computer):
        """
        An example service that's supposed to replicate the functionality of a webserver
        As of now (just for example purposes) it just echos args that is sent to it.
        """
        super().__init__("WebServer", 80, computer)

    def main(self, args: dict) -> Result:
        """
        Function that runs when the service is 'connected to'

        Args:
            args (dict): A dict of arguments that is given to the service to process

        Returns:
            Result: A `Result` object containing the success status and resulting data of the service
        """
        find_var_www_html = self.computer.fs.find("/var/www/html/index.html")

        if not find_var_www_html.success:
            return Result(success=True, data={})
        else:

            return Result(success=True, data={"content": find_var_www_html.data.content})
        # return Result(success=True, data={"args": args})
