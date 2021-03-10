from hashlib import md5
from typing import Union


class User:
    def __init__(self, username: str):
        """
        The base user class for users registered in a computer

        Args:
            username: users username (duh)
        """
        # Determined by the system
        self.uid = None
        self.username = username
        self.password = None
        # Extra fields that some linux distros store
        self.full_name = None
        self.room_number = None
        self.work_phone = None
        self.home_phone = None
        self.other = None

        # Groups the user is associated with
        self.groups = {}

    def set_password(self, password: Union[str, None] = None) -> None:
        """
        Sets the password for the current user
        Args:
            password (str, optional): The new plaintext password or None for no password

        Returns: None

        """
        if not password:
            self.password = None
        else:
            self.password = md5(password.encode()).hexdigest()

    def add_group(self, group: "Group"):
        if group.name not in self.groups.keys():
            self.groups[group.name] = group
            return True
        else:
            return False


class Group:
    def __init__(self, name: str, gid: int) -> None:
        """
        The object representing a group in a unix system

        Args:
            name (str): The name of the group
            gid (int): The group ID of the given group (calculated by the `Computer`)
        """
        self.name = name
        self.gid = gid
