from typing import Optional

from ..helpers import Result

computer: Optional["Computer"] = None


def update(comp: "Computer"):
    global computer
    computer = comp


def system(command: str, output: bool = True) -> Result:
    # Split the command and args
    split_command = command.split(" ")
    return computer.run_command(split_command[0], split_command[1:], not output)