from typing import Optional

from ..helpers import Result, ResultMessages
from ..helpers import passwd as passwd_internal
from ..user import User

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


# TODO: Maybe implement putspent for shadow file
def putpwent(entry: passwd) -> Result:
    if computer.sys_getuid() != 0:
        return Result(success=False, message=ResultMessages.NOT_ALLOWED)

    # If no user with pw_name doesn't exist, add a new user
    find_user_result = computer.get_user(username=entry.pw_name)

    if not find_user_result.success:
        computer.add_user(entry.pw_name, entry.pw_passwd, entry.pw_uid, plaintext=False)
        computer.add_user_to_group(entry.pw_uid, entry.pw_uid, membership_type="primary")
        return Result(success=True)

    user: User = find_user_result.data

    if user.password != entry.pw_passwd:
        computer.change_user_password(uid=user.uid, new_password=entry.pw_passwd, plaintext=False)

    if user.uid != entry.pw_uid:
        computer.change_user_uid(user.uid, entry.pw_uid)

    # TODO: Add the ability to change other values like homedir, etc

    computer.sync_user_and_group_files()

    return Result(success=True)
