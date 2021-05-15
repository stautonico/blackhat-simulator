from .service import Service
from ..helpers import Result, ResultMessages


class DNSServer(Service):
    def __init__(self, computer):
        super().__init__("DNSServer", 53, computer)
        self.dns_records = {}

    def add_dns_record(self, domain_name: str, ip: str) -> Result:
        """
        Add a new record to the given `ISPRouters` DNS records table

        Args:
            domain_name (str): The domain name of the record
            ip (str): The IP address that the given `domain_name` should resolve to

        Returns:
            Result: A `Result` with the `success` flag set appropriately.
        """
        if domain_name in self.dns_records.keys():
            return Result(success=False, message=ResultMessages.ALREADY_EXISTS)

        self.dns_records[domain_name] = ip
        return Result(success=True)

    def remove_dns_record(self, domain_name):
        """
        Remove an existing record from the given `ISPRouters` DNS records table

        Args:
            domain_name (str): The domain name of the record to be removed

        Returns:
            Result: A `Result` with the `success` flag set appropriately.
        """
        if domain_name in self.dns_records.keys():
            del self.dns_records[domain_name]
            return Result(success=True)

        return Result(success=False, message=ResultMessages.NOT_FOUND)

    def resolve_dns(self, domain_name: str) -> Result:
        """
        Find the IP address linked to the given `domain_name`

        Args:
            domain_name (str): The domain name to resolve

        Returns:
            Result: A `Result` with the `success` flag set appropriately. The `data` flag contains the resolved IP address if found.
        """
        dns_record = self.dns_records.get(domain_name, None)
        if dns_record:
            return Result(success=True, data=dns_record)

        # Failed to find
        return Result(success=False, message=ResultMessages.NOT_FOUND)

    def main(self, args: dict) -> Result:
        return self.resolve_dns(args.get("domain"))
