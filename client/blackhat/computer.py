from typing import Optional, Dict, List

from .fs import StandardFS
from .helpers import SysCallStatus, SysCallMessages
from .session import Session
from .user import User


class Computer:
    def __init__(self) -> None:
        self.parent: Optional[Computer] = None  # Router
        self.hostname: Optional[str] = None
        self.users: Dict[str, User] = {}
        self.sessions: List[Session] = []

        # Root user needs to be created before the FS is initialized (FS needs root to have a password to create /etc/passwd)
        self.create_root_user()

        self.fs: StandardFS = StandardFS(self)

    def set_hostname(self, hostname: str) -> None:
        # NOTE: This will change to "update hostname" when fs is implemented
        self.hostname = hostname

    def add_user(self, username: str, password: str) -> SysCallStatus:
        if username in self.users.keys():
            return SysCallStatus(success=False, message=SysCallMessages.ALREADY_EXISTS)
        new_user = User(username)
        new_user.set_password(password)
        self.users[username] = new_user
        return SysCallStatus(success=True)

    def delete_user(self, username: str) -> SysCallStatus:
        if username in self.users.keys():
            del self.users[username]
            return SysCallStatus(success=True)

        return SysCallStatus(success=False, )

    def create_root_user(self) -> None:
        # Add the root user with a random password
        # self.add_user("root", ''.join([choice(ascii_uppercase + digits) for _ in range(16)]))
        self.add_user("root", "password")
        # self.users["root"].add_group(Group("root"))
        # The root users doesn't get an UID automatically, it is manually assigned UID 0
        self.users["root"].uid = 0
