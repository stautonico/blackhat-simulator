import os

from ..computer import Computer
from ..helpers import SysCallStatus, SysCallMessages
from ..lib.output import output

__COMMAND__ = "apt"
__VERSION__ = "1.0.0"


def main(computer: Computer, args: list, pipe: bool) -> SysCallStatus:
    if len(args) == 0:
        return output(f"{__COMMAND__}: an argument is required", pipe, success=False,
                      success_message=SysCallMessages.MISSING_ARGUMENT)

    if "--version" in args:
        return output(f"{__COMMAND__} (blackhat coreutils) {__VERSION__}", pipe)

    if args[0] == "install":
        if computer.get_uid() != 0:
            return output(f"{__COMMAND__}: unable to install package, are you root?", pipe, success=False)
        else:
            if len(args) < 2:
                return output(f"{__COMMAND__}: operation 'install' requires an argument", pipe, success=False)
            # Check if the package we're trying to install exists
            exists_dirty = os.listdir("./blackhat/bin/")
            exists_clean = []
            for file in exists_dirty:
                if file not in ["__pycache__", "__init__.py"]:
                    exists_clean.append(file.replace(".py", ""))

            for to_install in args[1:]:
                if to_install not in exists_clean:
                    return output(f"{__COMMAND__}: Unable to locate package {to_install}", pipe, success=False)

            # TODO: Install the package

            return output(f"{__COMMAND__}: This would be a success message", pipe)


    # TODO: Add `apt remove`

    else:
        return output(f"{__COMMAND__}: invalid operation: {args[0]}", pipe, success=False)
