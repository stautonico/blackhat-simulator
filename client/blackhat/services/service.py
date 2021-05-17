from typing import Optional


class Service:
    def __init__(self, name: str, port: int, computer: "Computer") -> None:
        """
        Generic base template for all network services

        Args:
            name (str): The name of the given service
            port (int): The port that the given service run on
        """
        self.name: str = name
        """str: The name of the given service"""
        self.brand: Optional[str] = None
        """str: The company that makes the given service"""
        self.version: float = 1.0
        """float: The version of the given service (duh)"""
        self.description: Optional[str] = None
        """str: A brief description of the given service (used for network scanners)"""
        self.port: int = port
        """int: The port that the give service runs on"""
        self.computer = computer
        """Computer: The computer the service is running on"""

    def get_metadata(self):
        return {
            "name": self.name,
            "brand": self.brand,
            "version": self.version,
            "description": self.description,
        }
