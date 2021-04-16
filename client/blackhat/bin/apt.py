import os
from json import loads

from ..computer import Computer
from ..fs import File, Directory
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.input import ArgParser
from ..lib.output import output

__COMMAND__ = "apt"
__VERSION__ = "1.1"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    """
    # TODO: Add docstring for manpage
    """
    parser = ArgParser(prog=__COMMAND__)
    parser.add_argument("command")
    parser.add_argument("packages", nargs="+")
    parser.add_argument("--version", action="store_true", help=f"output version information and exit")

    args = parser.parse_args(args)

    if parser.error_message:
        if args.version:
            return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

        if not args.version and not args.command and not args.packages:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False,
                          success_message=SysCallMessages.MISSING_ARGUMENT)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        # Read the packages.json file to substitute packages with a list of their subpackages (if they have)
        with open("packages.json", "r") as f:
            all_packages = loads(f.read())
        if args.command == "install":
            # Make sure /usr/bin, /var/lib/dpkg and /etc/apt/sources.list exists
            find_usr_bin = computer.fs.find("/usr/bin")
            find_usr_lib_dpkg_status = computer.fs.find("/var/lib/dpkg/status")
            find_apt_sources = computer.fs.find("/etc/apt/sources.list")
            if not find_usr_bin.success or not find_usr_lib_dpkg_status.success or not find_apt_sources.success:
                # In reality, a snap error will occur but we don't have snap so just throw general error
                return output(
                    f"{__COMMAND__}: Failed to install packages, check /usr/bin, /var/lib/dpkg, and /etc/apt/",
                    pipe,
                    success=False)

            usr_bin: Directory = find_usr_bin.data
            status_file: File = find_usr_lib_dpkg_status.data
            sources_file: File = find_apt_sources.data

            # Now we need to contact each server in our sources.list and ask each server if they have the package we're looking for
            servers = sources_file.content.split("\n")

            while "" in servers:
                servers.remove("")

            outstanding_packages = args.packages.copy()

            for server in servers:
                split_server = server.split(":")
                if len(split_server) == 1:
                    port = 80
                else:
                    port = split_server[1]

                host = split_server[0]

                ask_server_result = computer.send_tcp(host, port, {"packages": [x for x in outstanding_packages]})
                if ask_server_result.success:
                    if ask_server_result.data.get("have"):
                        for package in ask_server_result.data.get("have"):
                            if package in outstanding_packages:
                                outstanding_packages.remove(package)

            arg_packages = {}

            for pkg in args.packages:
                if pkg in all_packages.keys():
                    for subpkg in all_packages[pkg]:
                        if arg_packages.get(pkg):
                            arg_packages[pkg].append(subpkg)
                        else:
                            arg_packages[pkg] = [subpkg]
                else:
                    if arg_packages.get("other"):
                        arg_packages["other"].append(pkg)
                    else:
                        arg_packages["other"] = [pkg]

            # Check if the package we're trying to install exists
            exists = [file.replace(".py", "") for file in os.listdir("./blackhat/bin/installable") if
                      file not in ["__init__.py", "__pycache__"]]

            # We want to install only the packages that we found (not outstanding)
            for pkg_group, packages in arg_packages.items():
                for pkg in packages:
                    # Create a list of already installed packages to determine if we should install it again
                    installed_packages = status_file.read(computer)
                    if installed_packages.success:
                        installed_packages = installed_packages.data.split("\n")
                    else:
                        installed_packages = []

                    if pkg not in exists or pkg in outstanding_packages:
                        print(f"Unable to locate package {pkg}")
                    else:
                        to_check = pkg if pkg_group == "other" else pkg_group
                        if to_check in installed_packages:
                            print(f"{to_check} is already at the newest version, skipping...")
                            if pkg_group != "other":
                                # If we're doing a package with subpackages, it'll print our error message multiple times
                                break
                            else:
                                continue
                        # Add the file to /usr/bin
                        current_file = File(pkg, "[BINARY DATA]", usr_bin, 0, 0)
                        usr_bin.add_file(current_file)
                        # We only want to store the package name if its not a subpackage
                        if pkg_group == "other":
                            status_file.append(pkg + "\n", computer)
                            print(f"Successfully installed package {pkg}")

                else:
                    if pkg_group != "other":
                        status_file.append(pkg_group + "\n", computer)
                        print(f"Successfully installed package {pkg_group}")

            computer.fs.generate_manpages()
            return output("", pipe)

        elif args.command == "remove":
            find_status_file = computer.fs.find("/var/lib/dpkg/status")
            if not find_status_file.success:
                return output(f"{__COMMAND__}: Unable to remove packages", pipe, success=False)

            status_file = find_status_file.data

            read_status = status_file.read(computer)

            if not read_status.success:
                return output(f"{__COMMAND__}: Unable to remove packages", pipe, success=False)

            installed_packages = [x for x in read_status.data.split("\n")]

            # Make sure all the packages we're trying to remove are actually installed
            for to_remove in args.packages:
                if to_remove not in installed_packages:
                    return output(f"{__COMMAND__}: Package '{to_remove}' is not installed, so not removed", pipe,
                                  success=False)

            for to_remove in args.packages:
                # Check if the package we're trying to remove has subpackages
                subpackages = all_packages.get(to_remove)
                if subpackages:
                    for subpkg in subpackages:
                        computer.run_command("rm", [f"/usr/bin/{subpkg}"], pipe)
                else:
                    computer.run_command("rm", [f"/usr/bin/{to_remove}"], pipe)
                    computer.run_command("rm", [f"/usr/share/man/{to_remove}"], pipe)
                installed_packages.remove(to_remove)

            # Update the content of /var/lib/dpkg/status
            status_file.write("\n".join(installed_packages), computer)

            return output(f"{__COMMAND__}: Successfully removed packages: {' '.join(args.packages)}", pipe)


        else:
            return output(f"{__COMMAND__}: invalid operation: {args.command}", pipe, success=False)
