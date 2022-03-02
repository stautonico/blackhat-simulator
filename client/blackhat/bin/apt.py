__package__ = "blackhat.bin"

import os
from json import loads

from ..helpers import Result
from ..lib.fcntl import creat
from ..lib.input import ArgParser
from ..lib.netdb import gethostbyname
from ..lib.output import output
from ..lib.sys import socket
from ..lib.sys.stat import stat
from ..lib.unistd import read, write, getuid

__COMMAND__ = "apt"
__DESCRIPTION__ = ""
__DESCRIPTION_LONG__ = ""
__VERSION__ = "1.0"


def parse_args(args=[], doc=False):
    """
    Handle parsing of arguments and flags. Generates docs using help from `ArgParser`

    Args:
        args (list): argv passed to the binary
        doc (bool): If the function should generate and return manpage

    Returns:
        Processed args and a copy of the `ArgParser` object if not `doc` else a `string` containing the generated manpage
    """
    parser = ArgParser(prog=__COMMAND__, description=f"{__COMMAND__} - {__DESCRIPTION__}")
    parser.add_argument("command")
    parser.add_argument("packages", nargs="+")
    parser.add_argument("--version", action="store_true", help=f"print program version")

    args = parser.parse_args(args)

    arg_helps_with_dups = parser._actions

    arg_helps = []
    [arg_helps.append(x) for x in arg_helps_with_dups if x not in arg_helps]

    NAME = f"**NAME*/\n\t{__COMMAND__} - {__DESCRIPTION__}"
    SYNOPSIS = f"**SYNOPSIS*/\n\t{__COMMAND__} [OPTION]... "
    DESCRIPTION = f"**DESCRIPTION*/\n\t{__DESCRIPTION_LONG__}\n\n"

    for item in arg_helps:
        # Its a positional argument
        if len(item.option_strings) == 0:
            # If the argument is optional:
            if item.nargs == "?":
                SYNOPSIS += f"[{item.dest.upper()}] "
            elif item.nargs == "+":
                SYNOPSIS += f"[{item.dest.upper()}]... "
            else:
                SYNOPSIS += f"{item.dest.upper()} "
        else:
            # Boolean flag
            if item.nargs == 0:
                if len(item.option_strings) == 1:
                    DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/\t{item.help}\n\n"
                else:
                    DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/\n\t\t{item.help}\n\n"
            elif item.nargs == "+":
                DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/=[{item.dest.upper()}]...\n\t\t{item.help}\n\n"
            else:
                DESCRIPTION += f"\t**{' '.join(item.option_strings)}*/={item.dest.upper()}\n\t\t{item.help}\n\n"

    if doc:
        return f"{NAME}\n\n{SYNOPSIS}\n\n{DESCRIPTION}\n\n"
    else:
        return args, parser


def main(args: list, pipe: bool) -> Result:
    args, parser = parse_args(args)

    if parser.error_message:
        if not args.version:
            return output(f"{__COMMAND__}: {parser.error_message}", pipe, success=False)

    # If we specific -h/--help, args will be empty, so exit gracefully
    if not args:
        return output("", pipe)
    else:
        if getuid() != 0:
            return output(f"{__COMMAND__}: error: you cannot perform this operation unless you are root.", pipe,
                          success=False)
        # Read the packages.json file to substitute packages with a list of their subpackages (if they have)
        with open("packages.json", "r") as f:
            all_packages = loads(f.read())
        if args.command == "install":
            # Make sure /usr/bin, /var/lib/dpkg and /etc/apt/sources.list exists
            read_usr_bin = stat("/usr/bin")
            read_usr_lib_dpkg_status = read("/var/lib/dpkg/status")
            read_apt_sources = read("/etc/apt/sources.list")
            if not read_usr_bin.success or not read_usr_lib_dpkg_status.success or not read_apt_sources.success:
                # In reality, a snap error will occur but we don't have snap so just throw general error
                return output(
                    f"{__COMMAND__}: Failed to install packages, check /usr/bin, /var/lib/dpkg, and /etc/apt/*",
                    pipe,
                    success=False)

            # Now we need to contact each server in our sources.list and ask each server if they have the package we're looking for
            servers = read_apt_sources.data.split("\n")

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

                resolve_hostname = gethostbyname(host)

                sock = socket.Socket(socket.AF_INET, socket.SOCK_STREAM)
                sock_addr = socket.SockAddr(socket.AF_INET, port, resolve_hostname.data.h_addr)
                connection_result = socket.connect(sock, sock_addr)

                if not connection_result.success:
                    return output(f"{__COMMAND__}: Unable to connect to {host}", pipe, success=False)

                ask_server_result = write(sock, {"packages": [x for x in outstanding_packages]})

                if ask_server_result.success:
                    for package in ask_server_result.data.keys():
                        if package in outstanding_packages:
                            # Loop through the directory structure and copy the files where they belong
                            outstanding_packages.remove(package)
                # print(ask_server_result.data["obtained"][0].files)

            return output("", success=True, pipe=pipe)

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
                    installed_packages = read_usr_lib_dpkg_status.data.split("\n")

                    while "" in installed_packages:
                        installed_packages.remove("")

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
                        current_file = creat(f"/usr/bin/{pkg}", 0o755)
                        write(f"/usr/bin/{pkg}", "[BINARY DATA]")
                        # We only want to store the package name if its not a subpackage
                        if pkg_group == "other":
                            print(f"Successfully installed package {pkg}")

                else:
                    if pkg_group != "other":
                        print(f"Successfully installed package {pkg_group}")

            return output("", pipe)
        #
        # elif args.command == "remove":
        #     find_status_file = computer.fs.find("/var/lib/dpkg/status")
        #     if not find_status_file.success:
        #         return output(f"{__COMMAND__}: Unable to remove packages", pipe, success=False)
        #
        #     status_file = find_status_file.data
        #
        #     read_status = status_file.read(computer)
        #
        #     if not read_status.success:
        #         return output(f"{__COMMAND__}: Unable to remove packages", pipe, success=False)
        #
        #     installed_packages = [x for x in read_status.data.split("\n")]
        #
        #     # Make sure all the packages we're trying to remove are actually installed
        #     for to_remove in args.packages:
        #         if to_remove not in installed_packages:
        #             return output(f"{__COMMAND__}: Package '{to_remove}' is not installed, so not removed", pipe,
        #                           success=False)
        #
        #     for to_remove in args.packages:
        #         # Check if the package we're trying to remove has subpackages
        #         subpackages = all_packages.get(to_remove)
        #         if subpackages:
        #             for subpkg in subpackages:
        #                 computer.run_command("rm", [f"/usr/bin/{subpkg}"], pipe)
        #         else:
        #             computer.run_command("rm", [f"/usr/bin/{to_remove}"], pipe)
        #             computer.run_command("rm", [f"/usr/share/man/{to_remove}"], pipe)
        #         installed_packages.remove(to_remove)
        #
        #     # Update the content of /var/lib/dpkg/status
        #     status_file.write("\n".join(installed_packages), computer)
        #
        #     return output(f"{__COMMAND__}: Successfully removed packages: {' '.join(args.packages)}", pipe)

        else:
            return output(f"{__COMMAND__}: invalid operation: {args.command}", pipe, success=False)
