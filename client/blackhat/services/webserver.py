from .service import Service
from ..helpers import SysCallStatus


class WebServer(Service):
    """
    An example service that's supposed to replicate the functionality of a webserver
    As of now (just for example purposes) it just echos args that is sent to it.
    """

    def __init__(self, computer):
        super().__init__("WebServer", 80, computer)

    def main(self, args: dict) -> SysCallStatus:
        find_var_www_html = self.computer.fs.find("/var/www/html/index.html")

        if not find_var_www_html.success:
            return SysCallStatus(success=True, data={})
        else:

            return SysCallStatus(success=True, data={"content": find_var_www_html.data.content})
        # return SysCallStatus(success=True, data={"args": args})
