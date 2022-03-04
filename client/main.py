import os
import pickle
import sys
from getpass import getpass

from blackhat.computer import Computer, Router, ISPRouter
from blackhat.services.aptserver import AptServer
from blackhat.services.sshserver import SSHServer
from blackhat.services.webserver import WebServer
from blackhat.session import Session
from blackhat.shell import Shell
from blackhat.services.dnsserver import DNSServer
from blackhat.services.whoisserver import WhoIsServer
from blackhat.fs import Directory, File

load_save_success = False

if "--debug" in sys.argv:
    os.environ["DEBUGMODE"] = "true"
    sys.argv.remove("--debug")
else:
    os.environ["DEBUGMODE"] = "false"

# Try to load the game from argv[1]
if len(sys.argv) > 1:
    try:
        with open(sys.argv[1], "rb") as f:
            comp = pickle.load(f)
            load_save_success = True
            comp.run_current_user_shellrc()
    except Exception:
        print("Failed to load save! Trying to load default save.")

elif "toload" in os.listdir():
    try:
        with open("toload", "r") as f:
            save_to_load = f.read().split("\n")[0]

        with open(save_to_load, "rb") as f:
            comp = pickle.load(f)
            os.remove("toload")
            load_save_success = True
            comp.run_current_user_shellrc()
    except Exception:
        print("Failed to load save! Trying to load default save.")

# If we couldn't load a specific save, lets try to load the default `blackhat.save` file
if not load_save_success:
    if "blackhat.save" in os.listdir():
        with open("blackhat.save", "rb") as f:
            comp = pickle.load(f)
        comp.run_current_user_shellrc()
    # Let's start a new game save
    else:
        comp = Computer()

        if "-u" in sys.argv:
            try:
                username = sys.argv[sys.argv.index("-u") + 1]
                sys.argv.remove("-u")
                sys.argv.remove(username)
            except IndexError:
                print(f"{__file__}: -u requires additional arguments")
                exit()
        else:
            username = input("Username: ")

        if "-p" in sys.argv:
            try:
                password = sys.argv[sys.argv.index("-p") + 1]
                sys.argv.remove("-p")
                sys.argv.remove(password)
            except IndexError:
                print(f"{__file__}: -p requires additional arguments")
                exit()
        else:
            while True:
                password = getpass()
                confirm = getpass("Confirm password: ")

                if password != confirm:
                    print("Passwords don't match!")
                else:
                    break

        # Create a temporary root session for initializing stuff
        session = Session(0, comp.fs.files, 0)

        comp.sessions.append(session)

        comp.run_command("adduser", ["steve", "-p", "password", "-n"], False)
        # comp.add_user(username, password)

        # Add user to /etc/sudoers file
        sudoers_file = comp.fs.find("/etc/sudoers").data

        sudoers_file.content += "steve ALL=(ALL) ALL"

        # Add `google.com` to our apt repos
        apt_source_file = comp.fs.find("/etc/apt/sources.list").data

        apt_source_file.content = "google.com\n"

        session = Session(1000, comp.fs.files, 0)

        # Tests for networking
        isp = ISPRouter()

        isp.wan = "1.1.1.1"

        lan = Router()

        other_comp = Computer()

        lan.add_new_client(comp)
        lan.add_new_client(other_comp)

        lan2 = Router()

        lan2_client1 = Computer()
        lan2_client2 = Computer()

        lan2.add_new_client(lan2_client1)
        lan2.add_new_client(lan2_client2)

        isp.add_new_client(lan)
        isp.add_new_client(lan2)

        print(f"LAN ROUTER: {lan.wan}")
        print(f"Self_comp: {comp.lan}")
        print(f"Other_comp: {other_comp.lan}")

        print("------------------------------------------")
        print(f"LAN2 ROUTER WAN ADDRESS: {lan2.wan}")
        print(f"LAN2 CLIENT1 LAN ADDRESS: {lan2_client1.lan}")
        print(f"LAN2 CLIENT2 LAN ADDRESS: {lan2_client2.lan}")

        comp.services[80] = WebServer(comp)

        other_comp.services[80] = WebServer(other_comp)
        other_comp.services[22] = SSHServer(other_comp)

        other_comp.sessions = [Session(0, other_comp.fs.files, 0)]
        other_comp.run_command("touch", ["/var/www/html/index.html"], pipe=True)
        other_comp.fs.find("/var/www/html/index.html").data.content = "<h1>Hello world!</h1>"

        lan2.sys_sethostname("google.com")

        lan2.services[2222] = SSHServer(lan2)

        lan2.port_forwarding = {2222: lan2, 22: lan2_client2, 80: lan2_client2}

        lan2_client2.services[80] = AptServer(lan2_client2)
        lan2_client2.services[22] = SSHServer(lan2_client2)

        # Create a temporary root session for initializing stuff
        lan2_client2.sessions = [Session(0, lan2_client2.fs.files, 0)]

        isp.services[53] = DNSServer(isp)
        isp.services[53].add_dns_record("google.com", lan2.wan)
        isp.services[43] = WhoIsServer(isp)
        isp.services[43].add_whois("google.com")
        isp.port_forwarding = {53: isp}

        # Setup our apt server
        # To setup an apt server, we need /var/www/html/repo
        # And inside the /repo folder, we need a file with the name of each package that the given server has for download
        # This example apt server has all the "installable" packages
        lan2_client2.run_command("mkdir", ["/var/www/html/repo"], pipe=True)
        lan2_client2.run_command("cd", ["/var/www/html/repo"], pipe=True)
        
        # Manually setup apt repo
        repo_dir = lan2_client2.fs.find("/var/www/html/repo")

        if repo_dir.success:
            repo_dir = repo_dir.data

            for package in ["netutils", "john", "nmap", "whois"]:
                if package == "netutils":
                    lan2_client2.run_command("mkdir", ["-p", "/var/www/html/repo/netutils/1.0/usr/bin"], pipe=True)
                    netutils_dir: Directory = lan2_client2.fs.find("/var/www/html/repo/netutils/1.0/usr/bin").data
                    for file in ["ping", "curl", "dig", "ifconfig"]:
                        with open(f"blackhat/bin/installable/{file}.py", "r") as f:
                            File(file, f.read(), netutils_dir, 0, 0)
                elif package == "john":
                    lan2_client2.run_command("mkdir", ["-p", "/var/www/html/repo/john/1.0/usr/bin"], pipe=True)
                    john_dir: Directory = lan2_client2.fs.find("/var/www/html/repo/john/1.0/usr/bin").data
                    for file in ["john", "unshadow"]:
                        with open(f"blackhat/bin/installable/{file}.py", "r") as f:
                            File(file, f.read(), john_dir, 0, 0)
                else:
                    lan2_client2.run_command("mkdir", ["-p", f"/var/www/html/repo/{package}/1.0/usr/bin"], pipe=True)
                    package_dir: Directory = lan2_client2.fs.find(f"/var/www/html/repo/{package}/1.0/usr/bin").data
                    with open(f"blackhat/bin/installable/{package}.py", "r") as f:
                        File(package, f.read(), package_dir, 0, 0)
                        lan2_client2.run_command("mkdir", ["-p", f"/var/www/html/repo/{package}/1.0/etc/{package}/"], pipe=True)
                        conf_directory = lan2_client2.fs.find(f"/var/www/html/repo/{package}/1.0/etc/{package}/").data
                        File(f"{package}.conf", "0x0", conf_directory, 0, 0)

        #
        # for file in os.listdir("./blackhat/bin/installable"):
        #     if file not in ["__init__.py", "__pycache__", "ping.py", "curl.py", "dig.py", "ifconfig.py", "john.py",
        #                     "unshadow.py"]:
        #         with open(f"./blackhat/bin/installable/{file}", "r") as f:
        #             source_code = f.read()
        #         file = file.replace(".py", "")
        #
        #         lan2_client2.run_command("touch", [file], pipe=True)
        #         new_file_object = lan2_client2.fs.find(f"/var/www/html/repo/{file}")
        #
        #         if new_file_object.success:
        #             new_file_object.data.content = source_code


        # lan2_client2.run_command("mkdir", ["netutils"], True)
        # lan2_client2.run_command("cd", ["netutils"], True)
        # lan2_client2.run_command("touch", ["ping", "curl", "dig", "ifconfig"], True)
        # lan2_client2.run_command("cd", [".."], True)
        #
        # lan2_client2.run_command("mkdir", ["john"], True)
        # lan2_client2.run_command("cd", ["john"], True)
        # lan2_client2.run_command("touch", ["john", "unshadow"], True)
        # lan2_client2.run_command("cd", [".."], True)

        # During our temporary root session, we want to install the current "installable" tool that's being developed
        # Just so I don't have to "sudo apt install [PACKAGE]" every time I wanna test it
        # This has to happen after we add our apt server to /etc/apt/sources.list and after the network is fully inited
        # but before we remove our temporary root session
        comp.run_command("apt", ["install", "nmap"], False)
        comp.run_command("apt", ["install", "john"], False)
        comp.run_command("apt", ["install", "whois"], False)
        comp.run_command("apt", ["install", "netutils"], False)

        comp.run_command("touch", ["/var/www/html/index.html"], False)
        comp.fs.find("/var/www/html/index.html").data.content = "<h1>Hello world!</h1>"

        # comp.run_command("touch", ["/usr/bin/ping"], False)
        # comp.run_command("touch", ["/usr/bin/ifconfig"], False)
        # comp.run_command("touch", ["/usr/bin/unshadow"], False)
        # comp.run_command("touch", ["/usr/bin/john"], False)
        # comp.run_command("touch", ["/usr/bin/dig"], False)
        # comp.run_command("touch", ["/usr/bin/curl"], False)

        # We're done initializing the user stuff, lets remove the root session
        # And drop the user into a shell of their own user
        comp.sessions = []
        lan2_client2.sessions = []

        comp.sessions.append(session)

        for computer in [comp, other_comp, lan2_client1, lan2_client2, lan, lan2]:
            computer.sync_user_and_group_files()

        shell = Shell(comp)  # We need to setup the shell BEFORE the shellrc because aliases are shell-level things

        comp.run_current_user_shellrc()
        comp.run_command("cd", ["~"], False)
        comp.run_command("export", ["PATH=/usr/bin:$PATH"], False)

# from blackhat.new_shell import NewShell
# shell = NewShell(comp)
# shell.main()

shell.main()
