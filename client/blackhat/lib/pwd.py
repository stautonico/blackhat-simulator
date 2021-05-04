from typing import Optional

from ..helpers import Result, ResultMessages
from ..helpers import passwd as passwd_internal

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


passwd = passwd_internal


def getpwent(username: str = None, uid: int = None) -> Result:
    if not username and not uid:
        users = []

        for user in computer.get_all_users().data:
            user_struct = passwd(user.username, user.password, user.uid, user.uid, home_dir=f"/home/{user.username}")
            users.append(user_struct)

        return Result(success=True, data=users)

    user_lookup = computer.get_user(username=username, uid=uid)

    if not user_lookup.success:
        return Result(success=False, message=ResultMessages.NOT_FOUND)

    user = user_lookup.data

    return Result(success=True,
                  data=passwd(user.username, user.password, user.uid, user.uid, home_dir=f"/home/{user.username}"))
