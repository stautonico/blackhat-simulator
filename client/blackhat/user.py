from typing import Optional


class User:
    def __init__(self, uid: Optional[int] = None, username: Optional[str] = None, password: Optional[str] = None,
                 full_name: Optional[str] = None, room_number: Optional[str] = None, work_phone: Optional[str] = None,
                 home_phone: Optional[str] = None, other: Optional[str] = None) -> None:
        """
        The object that represents a user in a `Computer`


        Notes:
            <ul>
                <li>MD5 is used for the user's password hash due to its popularity and because of the fact that it is
                considered cryptography weak</li>
                <li>Additionally, no salt is used to make them slightly easier to crack (its still a game after all)</li>
            </ul>

        Args:
            uid (int): The UID of the given `User`
            username (str): The username of the `User` (duh)
            password (str): The MD5 hash of the `User`s password
            full_name (str): The full name entered by the user when the `User` is created
            room_number (str): The room number entered by the user when the `User` is created
            work_phone (str): The work phone entered by the user when the `User` is created
            home_phone (str): The home phone entered by the user when the `User` is created
            other (str): Any additional information entered by the user when the `User` is created
        """
        self.uid: Optional[int] = uid
        """int: User ID assigned by the the computer"""
        self.username: str = username
        self.password: Optional[str] = password
        """str: The MD5 sum of the `User`'s password"""
        self.full_name: Optional[str] = full_name
        self.room_number: Optional[str] = room_number
        self.work_phone: Optional[str] = work_phone
        self.home_phone: Optional[str] = home_phone
        self.other: Optional[str] = other


class Group:
    def __init__(self, gid: Optional[int] = None, name: Optional[str] = None) -> None:
        """
        The object that represents a group in a `Computer`


        Args:
            gid (int): The group ID of the group
            name (str): The name of the group
        """
        self.gid: int = gid
        self.name: str = name
