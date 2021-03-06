from .service import Service
from ..fs import Directory
from ..helpers import Result, ResultMessages


class AptServer(Service):
    def __init__(self, computer):
        """
        Apt repository server that handles requests for installing packages

        NOTE: I have no clue how apt repos work, so this is my best guess from what I read in a medium article 🤷‍♂️
        # TODO: Create ability to install specific version of a package with apt install nmap=1.1
        """
        super().__init__("AptServer", 80, computer)

    def main(self, args: dict) -> Result:
        """
        Function that runs when the service is 'connected to'

        Args:
            args (dict): A dict of arguments that is given to the service to process

        Returns:
            Result: A `Result` object containing the success status and resulting data of the service
        """
        find_var_www_html_repo = self.computer.fs.find("/var/www/html/repo/")

        if not find_var_www_html_repo.success:
            return Result(success=True, data={})
        else:
            repo_dir: Directory = find_var_www_html_repo.data
            if args.get("packages"):
                packages_we_have = []
                packages_we_dont_have = []
                for package in args.get("packages"):
                    find_package = repo_dir.find(package)
                    if find_package:
                        # We want to check if its a directory (because then we then we pass all the packages within)
                        if find_package.is_directory():
                            for subpackage in find_package.files.keys():
                                packages_we_have.append(subpackage)
                        else:
                            packages_we_have.append(package)
                    else:
                        packages_we_dont_have.append(package)

                return Result(success=True, data={"have": packages_we_have, "dont_have": packages_we_dont_have})
            else:
                return Result(success=False, message=ResultMessages.MISSING_ARGUMENT)
