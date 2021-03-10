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
            </ul>

        Args:
            username (str): The users username (duh)
        """
        self.uid: Optional[int] = None
        """int: User ID assigned by the the computer"""
        self.username: str = username
        self.password: Optional[str] = None
        """str: The MD5 sum of the `User`'s password"""
        # TODO: Add groups
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

# NOTE: Groups are stored in /etc/group in this format:
"""
<GROUP_NAME>:<PASSWORD (usually 'x')>:<GID>:<USERNAMES_OF_USERS_IN_GROUP_SPLIT_BY_COMMA>
"""