__package__ = "blackhat.bin"

import os
from json import loads
from typing import List
from colorama import Fore

from ..fs import File, Directory
from ..helpers import Result
from ..lib.fcntl import creat
from ..lib.input import ArgParser
from ..lib.netdb import gethostbyname
from ..lib.output import output
from ..lib.sys import socket
from ..lib.sys.stat import stat
from ..lib.unistd import read, write, getuid, execvp

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


def flatten_list(not_flat_list):
    flat_list = []
    # Iterate through the outer list
    for element in not_flat_list:
        if type(element) is list:
            # If the element is of type list, iterate through the sublist
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list


def generate_tree(current_directory: Directory, current_path: str = None):
    if not current_path:
        current_path = "/" + current_directory.name
    output_paths = []

    for item_name, item in current_directory.files.items():
        if item.is_directory():
            output_paths.append(generate_tree(item, os.path.join(current_path, item_name)))
        else:
            output_paths.append((os.path.join(current_path, item_name), item))

    return flatten_list(output_paths)


def install_package(package: List[tuple[str, File]]) -> bool:
    for filepath, file in package:
        parent_path = "/".join(filepath.split("/")[:-1])
        # print(f"Installing {file.name} to {parent_path} with mode {str(oct(file.get_perm_octal()).replace('0o', ''))}")
        execvp("mkdir", ["-p", parent_path])
        # Make sure the folder was created
        if not stat(parent_path).success:
            return False

        current_file = creat(filepath, file.get_perm_octal())
        if not current_file.success:
            return False

        result = write(filepath, file.content)
        if not result:
            return False

    return True


def read_installed_packages():
    # Make sure /usr/bin, /var/lib/dpkg and /etc/apt/sources.list exists
    read_usr_lib_dpkg_status = read("/var/lib/dpkg/status")
    installed_packages = read_usr_lib_dpkg_status.data.split("\n")
    while "" in installed_packages:
        installed_packages.remove("")

    return installed_packages


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
            read_usr_lib_dpkg_status = read("/var/lib/dpkg/status")
            read_apt_sources = read("/etc/apt/sources.list")
            if not read_usr_lib_dpkg_status.success or not read_apt_sources.success:
                # In reality, a snap error will occur but we don't have snap so just throw general error
                return output(
                    f"{__COMMAND__}: Failed to install packages, check /usr/bin, /var/lib/dpkg, and /etc/apt/*",
                    pipe,
                    success=False)

            installed_packages = read_installed_packages()

            # Now we need to contact each server in our sources.list and ask each server if they have the package we're looking for
            servers = read_apt_sources.data.split("\n")

            while "" in servers:
                servers.remove("")

            outstanding_packages = args.packages.copy()
            # Remove duplicates
            outstanding_packages = list(dict.fromkeys(outstanding_packages))

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
                    print(f"{__COMMAND__}: Unable to connect to {host}")
                    # return output(f"{__COMMAND__}: Unable to connect to {host}", pipe, success=False)

                ask_server_result = write(sock, {"packages": [x for x in outstanding_packages]})

                if ask_server_result.success:
                    for package in ask_server_result.data["obtained"]:
                        structure = []
                        if package["name"] in outstanding_packages:
                            if package["name"] in installed_packages:
                                print(f"{package['name']} is already the newest version ({package['version']}).")
                                outstanding_packages.remove(package["name"])
                                continue  # Skip the rest

                            # Loop through the directory structure and copy the files where they belong
                            for inode_name, inode in package["data"].files.items():
                                structure += generate_tree(inode)
                            outstanding_packages.remove(package["name"])
                        # Install the package
                        print(f"Installing {package['name']}...", end=" ")
                        install_result = install_package(structure)
                        if install_result:
                            installed_packages = "\n".join(installed_packages + [package["name"]])
                            write("/var/lib/dpkg/status", installed_packages)
                            installed_packages = read_installed_packages()
                            print(Fore.GREEN + "success" + Fore.RESET)
                        else:
                            print(Fore.RED + "failed" + Fore.RESET)

                # At the end, if we have packages left over, report them
                for package in outstanding_packages:
                    print(f"{Fore.RED}E:{Fore.RESET} Unable to locate package {package}")

            return output("", pipe=pipe)


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
