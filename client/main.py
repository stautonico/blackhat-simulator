import os
import pickle
import sys
from getpass import getpass

from blackhat.computer import Computer, Router, ISPRouter
from blackhat.services.sshserver import SSHServer
from blackhat.services.webserver import WebServer
from blackhat.session import Session
from blackhat.shell import Shell

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
    except Exception as e:
        print(f"Failed to load save! Trying to load default save.")

elif "toload" in os.listdir():
    try:
        with open("toload", "r") as f:
            save_to_load = f.read().split("\n")[0]

        with open(save_to_load, "rb") as f:
            comp = pickle.load(f)
            os.remove("toload")
            load_save_success = True
            comp.run_current_user_shellrc()
    except Exception as e:
        print(f"Failed to load save! Trying to load default save.")

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

        other_comp.services[80] = WebServer(other_comp)
        other_comp.services[22] = SSHServer(other_comp)

        lan2.set_hostname("google.com")

        lan2.services[2222] = SSHServer(lan2)

        lan2.port_forwarding = {2222: lan2}

        # We're done initializing the user stuff, lets remove the root session
        # And drop the user into a shell of their own user
        comp.sessions = []

        comp.sessions.append(session)

        comp.update_passwd()
        comp.update_groups()
        comp.run_current_user_shellrc()
        comp.run_command("cd", ["~"], False)

        isp.add_dns_record("google.com", lan2.wan)

shell = Shell(comp)
shell.main()
