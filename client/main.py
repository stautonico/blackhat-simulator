import os
import pickle
import sys
from getpass import getpass

from blackhat.computer import Computer
from blackhat.session import Session
from blackhat.shell import Shell

load_save_success = False

# Try to load the game from argv[1]
if len(sys.argv) > 1:
    try:
        with open(sys.argv[1], "rb") as f:
            comp = pickle.load(f)
            load_save_success = True
            # TODO: .shellrc
            # comp.run_current_user_shellrc()
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
        # TODO: Run user's .shellrc here
    # Let's start a new game save
    else:
        comp = Computer()
        print("Create new user...")

        username = input("Username: ")

        while True:
            password = getpass()
            confirm = getpass("Confirm password: ")

            if password != confirm:
                print("Passwords don't match!")
            else:
                break

        comp.add_user(username, password)

        comp.update_passwd()
        # TODO: .shellrc
        comp.run_command("cd", ["~"], False)

shell = Shell(comp)
shell.main()

# comp = Computer()
#
# comp.add_user("steve", "password")
#
# session = Session(1000, comp.fs.files, 0)
# session.env = {"HOME": "/root", "PATH": "/bin:",
#                "PS1": "\\e[0;31m\\u\\e[0m@\\e[0;32m\\h\\e[0m:\\e[0;34m\\w\\\\e[0m\\$ "}
#
# comp.sessions.append(session)
#
# hostname_file_lookup = comp.fs.find("/etc/hostname")
#
# if hostname_file_lookup.success:
#     hostname_file = hostname_file_lookup.data
#     # print(hostname_file.pwd())
#     # print(f"Original hostname: {comp.hostname}")
#
#     hostname_file.content = "testserver"
#
#     # print(f"/etc/hostname changed but not updated: {comp.hostname}")
#     comp.update_hostname()
#     # print(f"/etc/hostname changed and updated: {comp.hostname}")
#
#     # hostname_file.delete(0)
#
#     # comp.update_hostname()
#     # print(f"/etc/hostname deleted and updated: {comp.hostname}")
#
# # else:
# # print(f"Unable to find hostname file!")
#
# # for uid, user in comp.users.items():
# #     print(f"UID: {uid} - Username: {user.username} - Password: {user.password}")
#
# shell = Shell(comp)
#
# shell.main()
