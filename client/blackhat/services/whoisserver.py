from .service import Service
from ..helpers import Result, ResultMessages


class WhoIsServer(Service):
    def __init__(self, computer):
        """
        A service that stores and returns WHOIS data about a domain name
        """
        super().__init__("WhoIsServer", 43, computer)
        self.whois_records = {}

    def add_whois(self, domain_name: str) -> None:
        """
        Add a new WHOIS record to the `Service`'s 'database"

        Args:
            domain_name (str): The domain name

        Returns:
            None
        """
        self.whois_records[domain_name] = {"domain_name": domain_name.upper()}

    def get_whois(self, domain_name: str) -> Result:
        """
        Get a whois record (by domain name)

        Args:
            domain_name (str): The domain name to search

        Returns:
            Result: A `Result` object with the `success` flag accordingly and the `data` flag containing the fields if successful
        """
        record = self.whois_records.get(domain_name)

        if not record:
            return Result(success=False, message=ResultMessages.NOT_FOUND)

        return Result(success=True, data=record)

    def main(self, args: dict) -> Result:
        """
        Function that runs when the service is 'connected to'

        Args:
            args (dict): A dict of arguments that is given to the service to process

        Returns:
            Result: A `Result` object containing the success status and resulting data of the service
        """
        return self.get_whois(args.get("domain"))
