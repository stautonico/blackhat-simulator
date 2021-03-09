import pickle
from typing import Union

from .users import User
from .fs import StandardFS


class Computer:
    """
    The main 'game object' that represents a computer in a network.
    The computers is the main container that holds the filesystem, networking attributes,
    services, users, etc.
    """

    def __init__(self) -> None:
        # Usually, the parent is the router in the network
        self.parent: Union[Computer, None] = None
        """The `Computer` one level up in the network (usually the router/gateway)"""
        # User's registered in the system
        self.users = {}
        # The computers file system
        self.fs = StandardFS()
        """The computers file system (Unix FHS) `StandardFS`"""

    # Technically, functions in the `Computer` class should be like unix syscalls
    # But some things are done just for convenience

    def init(self) -> None:
        """
        Runs all the initialization steps a computer needs to get setup

        Initialization steps needed when booting and loading from a save:
        <ul>
            <li>Set machine hostname</li>
            <li>Clear environment variables</li>
            <li>Clear command history (NOTE: might remove, left over from old demo)</li>
            <li>Start uptime counter</li>
            <li>Run current user's .shellrc (.bashrc/.zshrc equivalent)</li>
            </ul>
        Returns:
            None
        """
        """
        TODO:
            * Setup hostname
            * Clear environment vars
            * Clear command history (might not need, left over from old demo)
            * Start uptime counter
            * Run current user's .shellrc (.bashrc/.zshrc equivalent)
        """
        pass

    def add_user(self, username: str, password: str) -> User:
        """
        Adds a new user to the system
        Args:
            username (str): username for the new user
            password (str): plain text password for the new user

        Returns:
            User: `User` object for the new user
        """
        new_user = User(username)
        new_user.set_password(password)
        self.users[username] = new_user
        return new_user

    def remove_user(self, username: str) -> bool:
        """
        Removes a user from the system
        Args:
            username (str): Username of user to remove

        Returns:
            bool: `True` if user was removed successfully, otherwise `False`
        """
        if username in self.users.keys():
            del self.users[username]
            return True
        else:
            return False

    def create_root_user(self) -> None:
        """
        Creates the root user for the system

        This is done separately just because the root user is slightly different from "standard" users.
        Returns:
            None
        """
        # NOTE: root user has a simple password just for debugging usage
        self.add_user("root", "password")
        # The root users doesn't get an UID automatically, it is manually assigned UID 0
        self.users["root"].uid = 0

    def save(self, output_file: Union[str, None] = "save.h3x") -> bool:
        """
        Serializes all objects in the game and dumps it to a file for saving

        Args:
            output_file (str, optional): Save file to dump to

        Returns:
            bool: `True` if saved successfully, otherwise `False`
        """
        try:
            with open(output_file, "wb") as f:
                pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            return False