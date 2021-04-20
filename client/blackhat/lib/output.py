from typing import Optional

from ..helpers import SysCallStatus, SysCallMessages


def output(text: str, pipe: bool, success: bool = True,
           success_message: Optional[SysCallMessages] = None) -> SysCallStatus:
    """
    Handle output from binaries and system commands properly with pipe
    If pipe is `True` (we're passing the output of a command into the input of another), we don't want to print the output

    Args:
        text (str): The text to output/pass to the next command
        pipe (bool): If we're going to use pipe for the next command
        success (bool): If the command was successful or not
        success_message (SysCallMessages, optional): An extra parameter to give additional information about the result of a command

    Returns:
        SysCallStatus: A `SysCallStatus` object with information about the status of a command (success, success message, etc)
    """
    # If we're piping the output, we don't want to print the output
    # This function will handle all the logic for pipe/output
    if not pipe:
        if text != "":
            while text.endswith("\n"):
                text = text[:-1]
            print(text)
    else:
        if text != "":
            text = text + "\n"

    if text == "":
        text = None

    return SysCallStatus(success=success, message=success_message, data=text)
