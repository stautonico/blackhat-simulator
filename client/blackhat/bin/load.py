from ..computer import Computer
from ..helpers import SysCallStatus
from ..lib.output import output

__COMMAND__ = "load"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if len(args) == 0:
        return output(f"{__COMMAND__}: Missing file to load", pipe, success=False)

    if not args[0].endswith(".save"):
        args[0] += ".save"

    try:
        # Make sure the save location is readable
        with open(args[0], "r") as f:
            # Open the toload file which the game will load from
            with open("toload", "w") as load:
                # Write the filename to load from
                # The client checks if the 'toload' file has content which determines if we should load a game save or not
                load.write(args[0])
        return output(f"Successfully loaded {args[0]}. Please restart the game to load the save", pipe)
    except Exception as e:
        return output(f"{__COMMAND__}: Failed to load save: {args[0]}", pipe, success=False)
