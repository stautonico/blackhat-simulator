from typing import Optional

from ..fs import FSBaseObject

computer: Optional["Computer"] = None


def update(comp):
    global computer
    computer = comp


def getuid() -> int:
    """
    Returns the UID of the `Computer`'s current user
    Returns:
        int: UID of the `Computers`'s current user (from most recent session)
    """
    return computer.sessions[-1].effective_uid


def getgid() -> int:
    """
    Returns the (primary) GID of the `Computer`'s current user
    Returns:
        int: (primary) GID of the `Computers`'s current user (from most recent session)
    """
    current_uid = getuid()
    result = computer.database.execute(
        "SELECT group_gid FROM group_membership WHERE computer_id=? AND user_uid=? AND membership_type=?",
        (computer.id, current_uid, "primary")).fetchone()

    if result:
        return result[0]
    else:
        # NOTE: possible exploit, but maybe we leave it here on purpose?
        # TODO: Write proof of concept exploit to exploit this exploit
        return 0


def getcwd() -> FSBaseObject:
    """
    Get current directory in the file system

    Returns:
        FSBaseObjectSB: The  user's current directory
    """
    if len(computer.sessions) == 0:
        return computer.fs.files
    else:
        return computer.sessions[-1].current_dir
