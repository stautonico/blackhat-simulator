import sys
from typing import Literal, List

from .helpers import SysCallStatus, SysCallMessages


class FSBaseObject:
    """
    The base object in a file system

    Could be used as a base for a directory or a file. This is close to the equivalent of an Inode in unix.
    All variables that this class are shared by files and directories
    The `File` and `Directory` type have their own unique variables along with their unique ones (in the given child class)

    Args:
        name (str): Name of the inode
        parent (Directory): The `Directory` that the current file exists inside of
        owner (int): The UID of the file's owner
        group_owner (int): The GID of the file's owner group

    """

    def __init__(self, name: str, parent: "Directory", owner: int, group_owner: int) -> None:
        self.name = name
        self.permissions = {"read": ["owner", "group", "public"], "write": ["owner"], "execute": []}
        self.owner = owner
        self.group_owner = group_owner
        self.parent = parent

    def is_directory(self) -> bool:
        """
        Returns:
            bool: True if the given file is a directory, otherwise False
        """
        return type(self) == Directory

    def is_file(self) -> bool:
        """
        Returns:
            bool: True if the given file is a file, otherwise False
        """
        return type(self) == File

    def change_owner(self, caller_uid: int) -> SysCallStatus:
        """
        Changes the owner only if specific cases are met.

        The only people that are allowed to change the owner of a file are:
        <ul>
            <li>The root user (UID 0)</li>
            <li>The owner of the file</li>
        </ul>

        Args:
            caller_uid (int): The UID of the user trying to change the owner

        Returns:
            SysCallStatus: The status object that contains the success status of the function
        """
        if caller_uid == self.owner or caller_uid == 0:
            self.owner = caller_uid
            return SysCallStatus(True)
        else:
            return SysCallStatus(False, SysCallMessages.NOT_ALLOWED)

    def check_perm(self, perm: Literal["read", "write", "execute"], uid: int, groups: List[int]) -> bool:
        """
        Checks if the given user has a given permission

        Args:
            perm (str): The permission to check (`read`, `write`, `execute`)
            uid (int): The UID of the user to check against
            groups (list of int): The GIDs of the groups the user belongs to

        Returns:
            bool: If the given UID has the given permission in the current `FSBaseObject`, then `True`, otherwise `False`
        """
        # Check if the user is root, then just return `True` because root has all perms
        if uid == 0:
            return True

        # If public can, then don't even bother checking specific permissions
        if "public" in self.permissions[perm]:
            return True
        # Next, check if the users group is in the perm
        if "group" in self.permissions[perm]:
            if self.group_owner in groups:
                return True
        # Finally, check if the owner can, and check if the user is the owner
        elif "owner" in self.permissions[perm]:
            if self.owner == uid:
                return True

        # No permission (access denied)
        return False


class File(FSBaseObject):
    """
    The class that represents a file in the FS (binary, plain text, whatever)

    Args:
        name (str): The filename
        content (str): The content that the file contains
        parent (Directory): The `Directory` that the current file exists inside of
        owner (int): The UID of the file's owner
        group_owner (int): The GID of the file's owner group
    """

    # TODO: Implement `copy` function (maybe)

    def __init__(self, name: str, content: str, parent: "Directory", owner: int, group_owner: int) -> None:
        super().__init__(name, parent, owner, group_owner)
        self.content = content
        self.size = sys.getsizeof(content + name)

    def read(self, uid: int) -> SysCallStatus:
        """
        Checks if the user has the appropriate permissions, then returns the files content

        Args:
            uid (int): The UID of the user trying to read the file (usually current user)

        Returns:
            SysCallStatus: If success is `True`, `SysCallStatus.message` will contain the file's content
        """
        if self.check_perm("read", uid):
            return SysCallStatus(True, data=self.content)
        else:
            return SysCallStatus(False, message=SysCallMessages.NOT_ALLOWED)

    def write(self, uid: int, data: str) -> SysCallStatus:
        """
        Checks if the user has the appropriate permissions, then updates the file's content

        Args:
            uid (int): The UID of the user trying to write to the file (usually current user)
            data (str): The content to write to the file

        Returns:
            SysCallStatus: Success status depending on if the user had permissions to write to the file
        """
        if self.check_perm("write", uid):
            self.content = data
            self.update_size()
            return SysCallStatus(True)
        else:
            return SysCallStatus(False, message=SysCallMessages.NOT_ALLOWED)

    def append(self, uid: int, data: str) -> SysCallStatus:
        """
        Checks if the user has the appropriate permissions, then appends data to the end of the file's content

        Args:
            uid (int): The UID of the user trying to write to the file (usually current user)
            data (str): The content to write to the file

        Returns:
            SysCallStatus: Success status depending on if the user had permissions to write to the file
        """
        # NOTE: This may be unnecessary, we'll find out later
        if self.check_perm("write", uid):
            self.content += data
            self.update_size()
            return SysCallStatus(True)
        else:
            return SysCallStatus(False, message=SysCallMessages.NOT_ALLOWED)

    def update_size(self) -> None:
        """
        Recalculates the size of the file and tells it's parents to update their sizes (if applicable) (primarily used after updating a files content)
        Returns:
            None
        """
        # First, update our own size
        self.size = sys.getsizeof(self.content + self.name)
        # Now, recursively update our parent's size
        if self.parent:
            self.parent.update_size()


class Directory:
    pass


class StandardFS:
    pass
