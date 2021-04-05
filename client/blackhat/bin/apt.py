import os

from ..computer import Computer
from ..fs import File, Directory
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.output import output

__COMMAND__ = "apt"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: an argument is required", pipe, success=False,
                      success_message=SysCallMessages.MISSING_ARGUMENT)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if computer.get_uid() != 0:
        return output(f"{__COMMAND__}: Unable to acquire the dpkg lock (/var/lib/dpkg), are you root?", pipe,
                      success=False)

    if args[0] == "install":
        if len(args) < 2:
            return output(f"{__COMMAND__}: operation 'install' requires an argument", pipe, success=False)
        # Make sure /usr/bin, /var/lib/dpkg and /etc/apt/sources.list exists
        find_usr_bin = computer.fs.find("/usr/bin")
        find_usr_lib_dpkg_status = computer.fs.find("/var/lib/dpkg/status")
        find_apt_sources = computer.fs.find("/etc/apt/sources.list")
        if not find_usr_bin.success or not find_usr_lib_dpkg_status.success or not find_apt_sources.success:
            # In reality, a snap error will occur but we don't have snap so just throw general error
            return output(f"{__COMMAND__}: Failed to install packages, check /usr/bin, /var/lib/dpkg, and /etc/apt/",
                          pipe,
                          success=False)

        usr_bin: Directory = find_usr_bin.data
        status_file: File = find_usr_lib_dpkg_status.data
        sources_file: File = find_apt_sources.data

        # Now we need to contact each server in our sources.list and ask each server if they have the package we're looking for
        servers = sources_file.content.split("\n")

        while "" in servers:
            servers.remove("")

        outstanding_packages = args[1:]

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


        # Check if the package we're trying to install exists
        exists_dirty = os.listdir("./blackhat/bin/installable")
        exists_clean = []
        for file in exists_dirty:
            if file not in ["__pycache__", "__init__.py"]:
                exists_clean.append(file.replace(".py", ""))

        # We want to install only the packages that we found (not outstanding)
        for to_install in args[1:]:
            if to_install not in exists_clean or to_install in outstanding_packages:
                print(f"Unable to locate package {to_install}")
            else:
                # Add the file to /usr/bin
                current_file = File(to_install, "[BINARY DATA]", usr_bin, 0, 0)
                usr_bin.add_file(current_file)
                status_file.append(to_install, computer)
                print(f"Successfully installed package {to_install}")

        return output("", pipe)

    elif args[0] == "remove":
        find_status_file = computer.fs.find("/var/lib/dpkg/status")
        if not find_status_file.success:
            return output(f"{__COMMAND__}: Unable to remove packages", pipe, success=False)

        status_file = find_status_file.data

        read_status = status_file.read(computer)

        if not read_status.success:
            return output(f"{__COMMAND__}: Unable to remove packages", pipe, success=False)

        installed_packages = [x for x in read_status.data.split("\n")]

        # Make sure all the packages we're trying to remove are actually installed
        for to_remove in args[1:]:
            if to_remove not in installed_packages:
                return output(f"{__COMMAND__}: Package '{to_remove}' is not installed, so not removed", pipe,
                              success=False)

        for to_remove in args[1:]:
            computer.run_command("rm", [f"/usr/bin/{to_remove}"], pipe)
            installed_packages.remove(to_remove)

        # Update the content of /var/lib/dpkg/status
        status_file.write("\n".join(installed_packages), computer)

        return output(f"{__COMMAND__}: Successfully removed packages: {' '.join(args[1:])}", pipe)


    else:
        return output(f"{__COMMAND__}: invalid operation: {args[0]}", pipe, success=False)
