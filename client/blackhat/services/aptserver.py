from .service import Service
from ..fs import Directory
from ..helpers import Result, ResultMessages
from packaging import version as packaging_version


class AptServer(Service):
    def __init__(self, computer):
        """
        Apt repository server that handles requests for installing packages

        NOTE: I have no clue how apt repos work, so this is my best guess from what I read in a medium article 🤷‍♂️

        The apt server works as follows:
        The apt server stores a directory in /var/www/html/repo/ for each package.
        Inside each package directory is folder with a version number
        Inside each version number folder is a directory structure that contains the package files.
        The directory structure tells the client how to install the package.

        The client then sends a request to the apt server with the package name(s) and an optional version number.
        The apt server then checks if the package exists and if it does, it returns the directory structure.
        If the package doesn't exist, it returns an error message.

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
                output = {"obtained": [], "missing": []}

                for package in args.get("packages"):
                    # Check if we have a version number
                    if "=" in package:
                        package_name, version = package.split("=")
                    else:
                        package_name = package
                        version = None

                    # Check if the package exists
                    find_package = repo_dir.find(package_name)
                    if not find_package:
                        output["missing"].append(package_name)
                    else:
                        # Check if we have a version number
                        if version:
                            find_version = find_package.find(version)
                            if not find_version:
                                output["missing"].append(package)
                            else:
                                output["obtained"].append(find_version)
                        else:
                            # Find the most recent version number
                            # TODO: Find the proper version number and return
                            # print(f"LS RESULT!!!: ")
                            # execvp("ls", ["/var/www/html", "-l", "-a"])
                            read_dir = self.computer.fs.find(f"/var/www/html/repo/{package_name}")
                            if read_dir.success:
                                if len(read_dir.data.files) == 999:
                                    output["obtained"].append(read_dir.data.files[list(read_dir.data.files.keys())[0]])
                                else:
                                    filenames = list(read_dir.data.files.keys())

                                    # TODO: Keep a manifest of versions with dates to compare versions instead of parsing version numbers
                                    max_version = packaging_version.parse("0.0.0")

                                    for vers in filenames:
                                        parsed_version = packaging_version.parse(vers)
                                        if parsed_version > max_version:
                                            max_version = parsed_version

                                    output["obtained"].append(read_dir.data.files[str(max_version)])
                            else:
                                output["missing"].append(package_name)
                return Result(success=True, data=output)
            else:
                return Result(success=False, message=ResultMessages.MISSING_ARGUMENT)
