import importlib
import ipaddress
import os
import pickle
from random import choice, randint
from time import perf_counter
from typing import Optional, Dict, Union, List

from .fs import StandardFS, Directory, File
from .helpers import SysCallStatus, SysCallMessages
from .services.service import Service
from .session import Session
from .user import User, Group


class Computer:
    def __init__(self) -> None:
        """
        The class object representing a basic linux computer. This class is the base for all nodes on a network

        """
        self.boot_time = perf_counter()
        self.parent: Optional[Computer, Router, ISPRouter] = None  # Router
        self.hostname: Optional[str] = None
        self.users: Dict[int, User] = {}
        self.groups: Dict[int, Group] = {}
        self.sessions: List[Session] = []
        self.lan = None
        # Root user needs to be created before the FS is initialized (FS needs root to have a password to create /etc/passwd)
        self.create_root_user()

        self.fs: StandardFS = StandardFS(self)
        self.services: dict[int, Service] = {}
        self.init()

    def init(self):
        """
        Functions ran when a computer is booted

        Returns:
            None
        """
        self.update_hostname()

    def run_command(self, command: str, args: Union[str, List[str], None], pipe: bool) -> SysCallStatus:
        """
        Runs a system binary or an external binary

        Args:
            command (str): The command or binary to run
            args (list): A list of arguments passed to the command or binary
            pipe (bool): If a pipe was used (used for routing input/output)

        Returns:
            SysCallStatus: A `SysCallStatus` object that contains a success status and some response data (changed on a case-by-case basis)
        """
        # TODO: Instead of checking the bin_dir, check the `PATH` environment var (split by :) (do the same in `run_binary`)
        # The way that the path works is that if there are 2 binaries with the same name in 2 different directories,
        # The one that matches first in the path gets run
        # For example, if ls is in /etc/ and in /bin/ and the path is PATH=/home:/bin:/etc, the one in bin will run
        # For example, if ls is in /etc/ and in /bin/ and the path is PATH=/home:/etc:/bin, the one in etc will run
        bin_dir = self.fs.files.find("bin")
        if not bin_dir:
            print(f"{command}: command not found")
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        if command not in list(bin_dir.files.keys()):
            print(f"{command}: command not found")
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        try:
            module = importlib.import_module(f"blackhat.bin.{command}")
            response = module.main(self, args, pipe)
            if os.getenv("DEBUGMODE") == "false":
                self.save()

            return response
        except ImportError as e:
            print(f"There was an error when running command: {command}")
            return SysCallStatus(success=False, message=SysCallMessages.GENERIC)

    def update_hostname(self) -> None:
        """
        Reads /etc/hostname and sets the system hostname accordingly
        If /etc/hostname doesn't exist, the hostname is set to "localhost"

        Returns:
            None
        """
        etc_dir: Directory = self.fs.files.find("etc")

        if not etc_dir:
            self.hostname = "localhost"

        else:
            hostname_file: File = etc_dir.find("hostname")

            if not hostname_file:
                self.hostname = "localhost"
            else:
                self.hostname = hostname_file.content.split("\n")[0]

    def add_user(self, username: str, password: str, uid: Optional[int] = None) -> SysCallStatus:
        """
        Add a new user to the system.
        This function also generates the UID for the new user (unless manually specified)

        Args:
            username (str): The username for the new user
            password (str): The plaintext password for the new user
            uid (int, optional): The UID of the new user

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately. The `data` flag contains the new users UID if successful.
        """
        if self.user_exists(username).success:
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)
        new_user = User(username)
        new_user.set_password(password)

        # Manually specific UID
        if uid:
            if uid in self.users.keys():
                return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)
            else:
                next_uid = uid
        # Auto-generate the UID (depending on the situation)
        else:
            # We're creating our root user, there isn't going to be a previous UID
            if len(self.users.keys()) == 0:
                next_uid = 0
            else:
                last_uid = list(self.users.keys())[-1]
                if last_uid == 0:
                    next_uid = 1000
                else:
                    next_uid = last_uid + 1

        new_user.uid = next_uid
        self.users[next_uid] = new_user

        return SysCallStatus(success=True, data=next_uid)

    def delete_user(self, username: str) -> SysCallStatus:
        """
        Deletes a user from the system (by username)

        Args:
            username (str): The username of the user to delete

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately.
        """
        if self.user_exists(username).success:
            del self.users[username]
            return SysCallStatus(success=True)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def add_group(self, name: str, gid: Optional[int] = None) -> SysCallStatus:
        """
        Add a new group to the system.
        This function also generates the GID for the new group (unless manually specified)

        Args:
            name (str): The name for the new group
            gid (int, optional): The GID of the new user

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately. The `data` flag contains the GID if successful.
        """
        if self.group_exists(name).success:
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

        if gid:
            if gid in self.groups.keys():
                return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)
            else:
                new_group = Group(name, gid)
        else:
            # Auto-generate the GID (depending on the situation)
            if len(self.groups.keys()) == 0:
                next_gid = 0
            else:
                last_gid = list(self.groups.keys())[-1]
                if last_gid == 0:
                    next_gid = 1000
                else:
                    next_gid = last_gid + 1

            new_group = Group(name, next_gid)

        self.groups[new_group.gid] = new_group

        return SysCallStatus(success=True, data=new_group.gid)

    def delete_group(self, name: str) -> SysCallStatus:
        """
        Deletes a group from the system (by name)

        Args:
            name (str): The name of the group to delete

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately.
        """
        group_exists = self.group_exists(name)
        if group_exists.success:
            del self.groups[group_exists.data]
            return SysCallStatus(success=True)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def create_root_user(self) -> None:
        """
        Since the root user is different from "standard" users, and it must exist in any given system, it is manually
        created when the `Computer` is first initialized.

        Returns:
            None
        """
        # Add the root user with a random password
        # self.add_user("root", ''.join([choice(ascii_uppercase + digits) for _ in range(16)]))
        self.add_user("root", "password", 0)
        root_group = Group("root", 0)
        self.groups = {0: root_group}
        self.users[0].groups = [root_group]

    def update_passwd(self) -> SysCallStatus:
        """
        Makes sure that /etc/passwd matches our internal user map

        Returns:
            None
        """
        etc_dir: Directory = self.fs.files.find("etc")

        if not etc_dir:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        passwd_file: File = etc_dir.find("passwd")

        passwd_content = ""

        for uid, user in self.users.items():
            passwd_content += f"{user.username}:{user.password}:{uid}\n"

        if not passwd_file:
            # Create the /etc/passwd
            etc_dir.add_file(File("passwd", passwd_content, etc_dir, 0, 0))
        else:
            passwd_file.content = passwd_content

        return SysCallStatus(success=True)

    def update_groups(self) -> SysCallStatus:
        """
        Makes sure that /etc/group matches our internal groups map

        Returns:
            None
        """
        etc_dir: Directory = self.fs.files.find("etc")

        if not etc_dir:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

        group_file: File = etc_dir.find("group")

        group_content = ""

        for gid, group in self.groups.items():
            group_content += f"{group.name}:x:{gid}\n"

        if not group_file:
            # Create the /etc/groups
            etc_dir.add_file(File("group", group_content, etc_dir, 0, 0))
        else:
            group_file.content = group_content

        return SysCallStatus(success=True)

    def get_uid(self) -> int:
        """
        Returns the UID of the `Computer`'s current user
        Returns:
            int: UID of the `Computers`'s current user (from most recent session)
        """
        return self.sessions[-1].effective_uid

    def lookup_username(self, uid: int) -> SysCallStatus:
        """
        Find the username of a given user by UID

        Args:
            uid (int): The UID to lookup

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately. The `data` flag contains the user's username if found
        """
        if uid in self.users.keys():
            return SysCallStatus(success=True, data=self.users[uid].username)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def user_exists(self, username: str) -> SysCallStatus:
        """
        Check if a user exists in the `Computer` (by username)

        Args:
            username (str): The username of the user to check

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately (successful if found)
        """
        for user in self.users.values():
            if user.username == username:
                return SysCallStatus(success=True, data=user.uid)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def lookup_group(self, gid: int) -> SysCallStatus:
        """
        Find the group name of a given group by GID

        Args:
            gid (int): The GIT to lookup

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately. The `data` flag contains the groups name if found
        """
        if gid in self.users.keys():
            return SysCallStatus(success=True, data=self.groups[gid].name)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def group_exists(self, name: str) -> SysCallStatus:
        """
        Check if a group exists in the `Computer` (by name)

        Args:
            name (str): The name of the group to check

        Returns:
            SysCallStatus: A `SysCallStatus` instance with the `success` flag set appropriately (successful if found)
        """
        for group in self.groups.values():
            if group.name == name:
                return SysCallStatus(success=True, data=group.gid)
        else:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def run_current_user_shellrc(self):
        """
        Run the .shellrc file in the current user's home folder (/home/<USERNAME>/.shellrc)
        The ".shellrc" file is replicating the behavior of .bashrc/.bash_profile/.zshrc (since we're not replicating one specific piece of software)

        Returns:
            None
        """
        current_username = self.lookup_username(self.get_uid()).data

        # Don't check /home/username, check /root for .shellrc
        if self.get_uid() == 0:
            shellrc_loc = "/root/.shellrc"
        else:
            shellrc_loc = f"/home/{current_username}/.shellrc"

        shellrc_lookup = self.fs.find(shellrc_loc)

        if shellrc_lookup.success:
            shellrc_lines = shellrc_lookup.data.read(self.users[self.get_uid()])

            if shellrc_lines.success:
                for line in shellrc_lines.data.split("\n"):
                    if line != "":
                        line = line.split()
                        result = self.run_command(line[0], line[1:], pipe=False)

    def save(self, output_file: str = "blackhat.save") -> bool:
        """
        Serialize and dump the current `Computer` (and everything that's connected to it (`StandardFS`, `File`s, etc)) to a file
        Args:
            output_file (str, optional): The file to dump the contents to

        Returns:
            bool: `True` if the dump/save was successful, otherwise `False`
        """
        try:
            with open(output_file, "wb") as f:
                pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            return False

    def handle_tcp_connection(self, host: str, port: int, args: dict) -> SysCallStatus:
        """
        Route network traffic to a `Service` on the local `Computer`

        Args:
            host (str): The IP of the `Computer`
            port (int): The port the given `Service` in running on
            args (dict): A map of arguments to pass to the given `Service`

        Returns:
            SysCallMessage: A response generate by the `Service` or an error if no such `Service` exists.
        """
        if port in self.services.keys():
            return self.services[port].main(args)

        return SysCallStatus(success=False, message=SysCallMessages.GENERIC_NETWORK)

    def send_tcp(self, host: str, port: int, args: dict) -> SysCallStatus:
        """
        Pass a network connection to the router to route (either within the LAN or to an external LAN)

        Args:
            host (str): The IP address of the host to send the given `args` to
            port (int): The port on the given `host` in which the `Service` runs on
            args (dict): The data to send to the given `host` (processed by the `Service` on the other end)

        Returns:
            SysCallMessage: A response generate by the `Service` or an error if no such `Service` exists.
        """
        return self.parent.handle_tcp_connection(host, port, args)


class Router(Computer):
    def __init__(self) -> None:
        """
        This special type of `Computer` is made for handling network traffic between computers in a LAN
        This class represents what a real router would be in real life
        """
        super().__init__()
        self.clients = {}  # Format of clients: sorted by VLAN then ID [1][2] (VLAN 1 - ID 2)
        self.ip_pool: dict[int, list[str]] = {}
        self.wan = None
        self.lan = "192.168.1.1"
        self.port_forwarding = {}

    def dhcp(self, vlan: int) -> SysCallStatus:
        """
        Distributes IP addresses to clients on the network

        Args:
            vlan (int): VLAN id to assign the client to

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the IP to assign to a given client.
        """
        # Split the router's IP to get the first 16 bits
        ip_split = self.lan.split(".")
        network_prefix = f"{ip_split[0]}.{ip_split[1]}.{vlan}"

        # Check if the IP pool for that VLAN was generated already
        try:
            len(self.ip_pool[vlan])
        # If `self.ip_pool[<VLAN>]` returns a key error, it was never created before
        except KeyError:
            # Generate a list of ips that are <NETWORK_PREFIX>.<VLAN>.1-256
            self.ip_pool[vlan] = [f"{network_prefix}.{x}" for x in range(1, 257)]

        # Check if we have IP's left
        if len(self.ip_pool[vlan]) == 0:
            return SysCallStatus(success=False, message=SysCallMessages.EMPTY)

        # Choose a random ip from the pool
        ip = choice(self.ip_pool[vlan])

        # Remove the IP from the pool since it's in use
        self.ip_pool[vlan].remove(ip)
        return SysCallStatus(success=True, data=ip)

    def find_local_client(self, ip: str) -> SysCallStatus:
        """
        Finds a client (`Computer` object) in the local network by IP address

        Args:
            ip (str): The "private" IP of the client `Computer` to find

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `Computer` object if found.
        """
        vlan = ip.split(".")[2]
        for client in self.clients[int(vlan)].values():
            if client.lan == ip:
                return SysCallStatus(success=True, data=client)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def find_client(self, ip: str, port: Optional[int] = None) -> SysCallStatus:
        """
        A more "general" version of the `find_local_client()` function. This function determines if the given router will
        ask the `ISPRouter` for the given IP address or if the client is within the `Router`'s LAN

        Args:
            ip (str): The IP of the client `Computer` to find
            port (int, optional): The open port on the given client (find `Computer` behind another `Router` in an external LAN)

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `Computer` object if found.
        """
        # Check if the client belongs to ourselves (don't ask isp)
        ip_split = self.lan.split(".")
        network_prefix = f"{ip_split[0]}.{ip_split[1]}"

        # We're looking for ourselves
        if ip == self.lan:
            return SysCallStatus(success=True, data=self)

        if ip.startswith(network_prefix):
            return self.find_local_client(ip)

        # If the given ip is our wan address, another router is asking for a client by port
        if ip == self.wan:
            # If there's no port, we want the router
            if not port:
                return self.find_client(ip)
            else:
                # We specified a port, we're not looking for the router, we want a client being the router

                return self.find_client_by_port(port)
        # We're trying to find a client on another router, we do this by asking our router (the isp)
        else:
            wan_client = self.parent.find_client(ip, port)
            if wan_client.success:
                # We found the ip of the other router
                # If theres no port, we're done
                if not port:
                    return SysCallStatus(success=True, data=wan_client)
                else:
                    # If there is a port, we want the client behind that port
                    # Now let's directly ask that router whats on the given port
                    return wan_client.data.find_client(ip, port)
            else:
                # Even the ISP couldn't find the IP, it must not exist
                return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def find_client_by_port(self, port: int) -> SysCallStatus:
        """
        Find a client in the given `Router`'s LAN by open port.
        Primarily used for finding the `Computer` hosting a given `Service` through an open port in the given `Router`

        Args:
            port (int): The port number (1-65535) of the given `Computer`

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `Computer` object if found.
        """
        ip_to_find = self.port_forwarding.get(port, None)
        if not ip_to_find:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        vlan = ip_to_find.split(".")[2]
        for client in self.clients[int(vlan)].values():
            if client.lan == ip_to_find:
                return SysCallStatus(success=True, data=client)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def add_new_client(self, client: Computer, vlan: int = 1) -> SysCallStatus:
        """
        Connect a given `Computer` to the given `Router`'s LAN.
        Also, assign an IP address using the `dhcp()` function.

        Args:
            client (Computer): The `Computer` instance to connect to the `Router`'s LAN
            vlan (int, optional): The VLAN id to assign the given `Computer` to

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `client`'s newly assigned IP address if successful.
        """
        # Generate an IP for the client
        generate_ip_status = self.dhcp(vlan)
        # We we're unable to generate an IP for the given client
        if not generate_ip_status:
            return generate_ip_status

        # Assign the IP
        client.lan = generate_ip_status.data

        # Append to client to our client list
        try:
            last_id = list(self.clients[vlan].keys())[-1]
        except KeyError:
            last_id = 0

        # Check if the client vlan exists
        try:
            len(self.clients[vlan])
        except KeyError:
            # Init the vlan (empty)
            self.clients[vlan] = {}

        self.clients[vlan][last_id + 1] = client

        client.parent = self

        return SysCallStatus(success=True, data=client.lan)

    def resolve_dns(self, domain_name: str) -> SysCallStatus:
        """
        Ask the ISP to resolve a dns domain name to an IP address

        Args:
            domain_name (str): The domain name to resolve

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the IP of the given `domain_name` if found.
        """
        # Ask our parent (ISP router) to resolve a dns record
        return self.parent.resolve_dns(domain_name)

    def handle_tcp_connection(self, host: str, port: int, args: dict) -> SysCallStatus:
        """
        Handle network traffic routing within the `Router`'s LAN and between LANs

        Args:
            host (str): The IP address of the host to send the given `args` to
            port (int): The port on the given `host` in which the `Service` runs on
            args (dict): The data to send to the given `host` (processed by the `Service` on the other end)

        Returns:
            SysCallStatus: A `SysCallStatus` instance containing results about the connection (successful or not) and a response from the `Service` (if successful)
        """
        # If we don't manually check for our own ip, we end up in an infinite loop of trying to handle tcp connections
        if host == self.lan:
            if port in self.services.keys():
                return self.services[port].main(args)
            else:
                return SysCallStatus(success=False, message=SysCallMessages.GENERIC_NETWORK)
        client = self.find_client(host, port)
        if not client.success:
            return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
        else:
            return client.data.handle_tcp_connection(host, port, args)


class ISPRouter(Router):
    def __init__(self):
        """
        An ISP router is just a router of routers
        """
        super().__init__()
        # We're 1.1.1.1
        self.used_ips = ["1.1.1.1"]
        self.dns_records = {}

    def dhcp(self, **kwargs) -> SysCallStatus:
        """
        Distributes IP addresses to clients on the network

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the IP to assign to a given client.
        """
        while True:
            ip = ".".join([str(randint(1, 256)) for _ in range(4)])
            if ip not in self.used_ips:
                self.used_ips.append(ip)
                return SysCallStatus(success=True, data=ip)

    def find_client(self, ip: str, port: Optional[int] = None) -> SysCallStatus:
        """
        Finds a client `Computer` in connected to the given `ISPRouter`

        Args:
            ip (str): The IP of the client `Computer` to find
            port (int, optional): The open port on the given client (find `Computer` behind another `Router` in an external LAN)

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `Computer` object if found.
        """
        # Check if the computer we're looking for is ourselves (isp)
        if ip == self.lan:
            return SysCallStatus(success=True, data=self)

        # Check if the client is an IP or a domain
        try:
            is_ipv4 = ipaddress.ip_address(ip)
        except ValueError:
            is_ipv4 = False

        if not is_ipv4:
            # Try to resolve the given dns record
            dns_result = self.resolve_dns(ip)

            if not dns_result.success:
                return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
            else:
                ip = dns_result.data

        find_client = next((x for x in self.clients.values() if x.wan == ip), None)
        if find_client:
            return SysCallStatus(success=True, data=find_client)

        # Client not found
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def add_new_client(self, client: Router, **kwargs) -> SysCallStatus:
        """
        Connect a given `Computer` to the given `ISPRouter`
        Also, assign an IP address using the `dhcp()` function.

        Args:
            client (Computer): The `Computer` instance to connect to the `ISPRouter`

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the `client`'s newly assigned IP address if successful.
        """
        dhcp_result = self.dhcp()
        if dhcp_result.success:
            client.wan = dhcp_result.data
            client.parent = self
            self.clients[client.wan] = client
            return SysCallStatus(success=True, data=client.wan)
        else:
            # Failed for some reason (DHCP will give us our error)
            return dhcp_result

    def add_dns_record(self, domain_name: str, ip: str) -> SysCallStatus:
        """
        Add a new record to the given `ISPRouters` DNS records table

        Args:
            domain_name (str): The domain name of the record
            ip (str): The IP address that the given `domain_name` should resolve to

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately.
        """
        if domain_name in self.dns_records.keys():
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)

        self.dns_records[domain_name] = ip
        return SysCallStatus(success=True)

    def remove_dns_record(self, domain_name):
        """
        Remove an existing record from the given `ISPRouters` DNS records table

        Args:
            domain_name (str): The domain name of the record to be removed

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately.
        """
        if domain_name in self.dns_records.keys():
            del self.dns_records[domain_name]
            return SysCallStatus(success=True)

        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)

    def resolve_dns(self, domain_name: str) -> SysCallStatus:
        """
        Find the IP address linked to the given `domain_name`

        Args:
            domain_name (str): The domain name to resolve

        Returns:
            SysCallStatus: A `SysCallStatus` with the `success` flag set appropriately. The `data` flag contains the resolved IP address if found.
        """
        dns_record = self.dns_records.get(domain_name, None)
        if dns_record:
            return SysCallStatus(success=True, data=dns_record)

        # Failed to find
        return SysCallStatus(success=False, message=SysCallMessages.NOT_FOUND)
