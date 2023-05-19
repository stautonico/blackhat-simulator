from blackhat.fs import Filesystem

class FSMapping:
    """
    A class that represents a mapping of a filesystem or other device to a path on the computer.
    """

    def __init__(self, path: str, filesystem: Filesystem):
        self._path: str = path
        self._filesystem: Filesystem = filesystem

        self._filesystem.add_mapping(path)

    def find(self, path: str):
        """
        Find a file or directory in the filesystem.
        :param path: The path to find
        :return: The file or directory that was found
        """
        return self._filesystem.find(path)
