import readline
from typing import List


class Shell:
    def __init__(self, computer):
        """
        The Shell object that allows the user to interact with the computer

        Notes:
            Will be removed once the GUI is working
            The GUI will replace the actual terminal

        Args:
            computer: The computer that the shell will interact with
        """
        self.computer = computer
        self.remote_computer = None
        self.prompt = self.generate_prompt()

        # Set autocomplete
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.autocomplete)

    def generate_prompt(self) -> str:
        """
        Generate the input prompt for the shell using the Bash PS1 environment variable
        Returns:
            str: The generated/formatted prompt
        """
        # TODO: Handle `PS1` for shell prompts
        return "steve@computer: "

    def autocomplete(self, text: str, state) -> List[str]:
        return []

    def run_command(self, command, args, external_binary, pipe):
        if external_binary:
            response = self.computer.run_binary(command, args, pipe)
        else:
            response = self.computer.run_command(command, args, pipe)
        self.prompt = self.generate_prompt()
        return response

    def try_run_command(self, command: str, args: list, pipe: bool = False):
        external_binary = False
        # Try to flatten the list of args to make one list (just in case)
        flat_args = []
        flatten = False
        # Only flatten the args if a list exists in the current args
        # TODO: Find a faster way to do this
        for arg in args:
            if type(arg) == list:
                flatten = True
                break

        if flatten:
            for sublist in args:
                for item in sublist:
                    flat_args.append(item)
        else:
            flat_args = args

        # Check if the command is an external binary (external from /bin)
        if command.startswith("./"):
            # External binaries that are not in the /bin dir
            # Remove the ./ to pass to the computer object
            command = command.replace("./", "")
            external_binary = True

        try:
            result = self.run_command(command, flat_args, external_binary, pipe)
            if result["success"]:
                return result["message"]
            else:
                return False
        except IndexError as e:
            print(e)
            print("error running command")

    def handle_command(self, command: str) -> None:
        """
        Decides what to do with the given `command` (input from user)

        Args:
            command (str): The command from the user (may contain pipes, redirections, etc)

        Returns:
            None
        """
        command = command.split()

        # Filter out extra spaces
        while "" in command:
            command.remove("")

        # Technically, the command to run should be the first item in the list
        command_name = command[0]

        args = command[1:]

        # Easy cases if there are no special characters
        if "|" not in command and ">" not in command and ">>" not in command:
            # We only pass "command" because we already removed the initial command name (and saved it)
            self.try_run_command(command_name, args, False)
        else:
            # Save the result from the previous command (used for pipes)
            prev_command_result = None

            # Keep going while we still have commands in our args array
            while True:
                for arg in args:
                    # Check if we have a special character (|, >, >>) because we need to handle it differently
                    if arg in ["|", ">", ">>"]:
                        # It doesn't matter if they're are multiple instances
                        # we only want the first because we delete stuff as we use it
                        current_index = args.index(arg)
                        special_character = command[current_index]
                        break
                else:
                    # We found no special characters so we must be at the last command,
                    # just run it like normal since we're not doing anything
                    # special after the fact
                    if len(args) == 0:
                        self.try_run_command(command_name, prev_command_result, False)
                    break

                # Our current list of args (for our current command) starts at the beginning of the list
                # and ends at the special character
                current_args = args[0:current_index]

                if prev_command_result:
                    if type(prev_command_result) == list:
                        command_result = self.try_run_command(command_name, current_args + prev_command_result, True)
                    else:
                        command_result = self.try_run_command(command_name,
                                                              current_args + [prev_command_result], True)
                else:
                    command_result = self.try_run_command(command_name, current_args, True)

                # Remove everything up to the current index (including the special character) (for the next cycle)
                del args[0:current_index + 1]

                # Don't bother running if the command failed (pipe chain doesn't continue if the command failed)
                if command_result:
                    # If the special character is > (write output) or >> (append output)
                    # We expect the next character in the command to be the file to write/append to
                    if special_character in [">", ">>"]:
                        # We expect the next item after the >/>> to be the file name to write/append to
                        filename_to_write_to = args[0]
                        # Try to remove extra spaces from the given filename
                        filename_to_write_to = filename_to_write_to.replace(" ", "")

                        # TODO: Write to the file
                        prev_command_result = None
                # Pass the output of the previous command to the input of the next command
                elif special_character == "|":
                    prev_command_result = command_result
                    prev_command_result = prev_command_result.split()
                    command_name = args[0]
                    del args[0]

    def main(self) -> None:
        """
        Starts the main "gameloop" for the given computer
        Returns:
            None
        """
        while True:
            command = input(self.prompt)

            if command:
                # Split by && and run individually
                for cmd in command.split("&&"):
                    self.handle_command(cmd)
