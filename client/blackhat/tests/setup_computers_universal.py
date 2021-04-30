from ..computer import Computer, Router, ISPRouter
from ..services.aptserver import AptServer
from ..services.sshserver import SSHServer
from ..services.webserver import WebServer
from ..session import Session
from ..shell import Shell



def init():
    computer = Computer()
    # Create a temporary root session for initializing stuff
    session = Session(0, computer.fs.files, 0)
    computer.sessions.append(session)
    computer.run_command("adduser", ["steve", "-p", "password", "-n"], False)

    # Add user to /etc/sudoers file
    sudoers_file = computer.fs.find("/etc/sudoers").data

    sudoers_file.content += "steve ALL=(ALL) ALL"

    # Add `google.com` to our apt repos
    apt_source_file = computer.fs.find("/etc/apt/sources.list").data

    apt_source_file.content = "google.com\n"

    session = Session(1000, computer.fs.files, 0)

    computer.sessions = []

    computer.sessions.append(session)

    computer.sync_user_and_group_files()

    computer.run_current_user_shellrc()
    computer.run_command("cd", ["~"], False)
    computer.run_command("export", ["PATH=/usr/bin:$PATH"], False)

    return computer