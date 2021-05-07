from typing import Optional, Union

from ..helpers import Result, ResultMessages

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


def system(command: str, output: bool = True) -> Result:
    # Split the command and args
    split_command = command.split(" ")
    return computer.run_command(split_command[0], split_command[1:], not output)


# TODO: Maybe implement `int overwrite` argument?
def setenv(name: str, value: str) -> Result:
    return computer.set_env(name, value)


def unsetenv(key: str) -> Result:
    if len(computer.sessions) == 0:
        return Result(success=False, message=ResultMessages.GENERIC)

    if key in computer.sessions[-1].env:
        del computer.sessions[-1].env[key]

    return Result(success=True)


def get_env(key: Optional[str] = None) -> Optional[Union[str, dict]]:
    if key:
        return computer.get_env(key)

    return computer.sessions[-1].env

def exit(force=False) -> None:
    computer.sys_exit(force)
