class Session:
    def __init__(self, uid: int, current_dir, id: int) -> None:
        """
        A open shell session in a given `Computer`
        Args:
            uid (int): The UID of the user logging in to the given `Session`
            current_dir (Directory): The current directory that the user is interacting with
            id (int): An internal only id (primarily used for naming pts sessions)
        """
        self.real_uid = uid
        """The 'original' user ID of the logged in user"""
        self.effective_uid = uid
        """A 'fake' user ID temporarily assigned to a user when running a command (while using sudo, etc)"""
        self.id = id
        """An internal only id (primarily used for naming pts sessions)"""

        self.current_dir = current_dir
        """The current directory that the user is interacting with"""

        self.env = {"PATH": "/bin:/usr/bin"}
        """The map of environment variables in the current session"""
