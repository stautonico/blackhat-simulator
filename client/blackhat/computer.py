from typing import Optional, Dict, List

from .fs import StandardFS, Directory, File
from .helpers import SysCallStatus, SysCallMessages
from .session import Session
from .user import User


class Computer:
    def __init__(self) -> None:
        self.parent: Optional[Computer] = None  # Router
        self.hostname: Optional[str] = None
        self.users: Dict[int, User] = {}
        # self.sessions: List[Session] = []
        self.env = {}
        # Root user needs to be created before the FS is initialized (FS needs root to have a password to create /etc/passwd)
        self.create_root_user()

        self.fs: StandardFS = StandardFS(self)

        self.current_dir = self.fs.files

        self.init()

    def init(self):
        self.update_hostname()

    def update_hostname(self) -> None:
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
        if username in self.users.keys():
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
        return SysCallStatus(success=True)

    def delete_user(self, username: str) -> SysCallStatus:
        if username in self.users.keys():
            del self.users[username]
            return SysCallStatus(success=True)

        return SysCallStatus(success=False, )

    def create_root_user(self) -> None:
        # Add the root user with a random password
        # self.add_user("root", ''.join([choice(ascii_uppercase + digits) for _ in range(16)]))
        self.add_user("root", "password", 0)
        # self.users["root"].add_group(Group("root"))

    def update_passwd(self) -> None:
        """
        Makes sure that /etc/passwd matches our internal user map

        Returns:
            None
        """
        etc_dir: Directory = self.fs.files.find("etc")
        passwd_file: File = etc_dir.find("passwd")

        passwd_content = ""

        for uid, user in self.users.items():
            passwd_content += f"{user.username}:{user.password}:{uid}"

        if not passwd_file:
            # Create the /etc/passwd
            etc_dir.add_file(File("passwd", passwd_content, etc_dir, 0, 0))
        else:
            passwd_file.content = passwd_content
