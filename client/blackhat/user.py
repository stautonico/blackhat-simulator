from hashlib import md5
from typing import Optional


class User:
    def __init__(self, username: str) -> None:
        """
        The object that represents a user in a `Computer`


        Notes:
            <ul>
                <li>MD5 is used for the user's password hash due to its popularity and because of the fact that it is
                considered cryptography weak</li>
                <li>Additionally, no salt is used to make them slightly easier to crack (its still a game after all)</li>
            </ul>

        Args:
            username (str): The users username (duh)
        """
        self.uid: Optional[int] = None
        """int: User ID assigned by the the computer"""
        self.username: str = username
        self.password: Optional[str] = None
        """str: The MD5 sum of the `User`'s password"""
        self.groups: list[int] = []
        self.full_name: Optional[str] = None
        self.room_number: Optional[str] = None
        self.work_phone: Optional[str] = None
        self.home_phone: Optional[str] = None
        self.other: Optional[str] = None

    def set_password(self, password: str = None) -> None:
        """
        Hashes (MD5) the given plain text password and saves it to the instance

        Args:
            password (str): The new plain text password

        Returns:
            None
        """
        if not password:
            self.password = None
        else:
            self.password = md5(password.encode()).hexdigest()

    def add_group(self, gid: int) -> None:
        """
        Add a group to the `User`'s group list

        Args:
            gid (int): Group ID of the group

        Returns:
            None
        """
        if gid not in self.groups:
            self.groups.append(gid)

    def remove_group(self, gid: int) -> None:
        """
        Remove a group from the `User`'s group list

        Args:
            gid (int): Group ID of the group

        Returns:
            None
        """
        if gid in self.groups:
            self.groups.remove(gid)


class Group:
    def __init__(self, name: str, gid: int) -> None:
        """
        The object that represents a group in a `Computer`


        Args:
            name (str): The name of the group
            gid (int): The group ID of the group
        """
        self.name: str = name
        self.gid: int = gid
