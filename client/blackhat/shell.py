import readline
from datetime import datetime

from colorama import Fore, Style, Back

from .computer import Computer


class Shell:
    def __init__(self, computer: Computer) -> None:
        """
        A temporary class that takes the place of the user's shell
        This will be removed once the GUI is working

        Args:
            computer (Computer): The `Computer` that the given `Shell` interacts with
        """
        self.computer: Computer = computer
        self.ssh_computer = None
        self.prompt: str = self.generate_prompt()

        # Setup tab to auto complete
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.autocomplete)

    def autocomplete(self, text, state):
        bin_dir_result = self.computer.fs.find("/bin")

        if bin_dir_result.success:
            commands = list(bin_dir_result.data.files.keys())
        else:
            commands = []

        results = [x for x in commands if x.startswith(text)] + [None]
        return results[state]

    def generate_prompt(self) -> str:
        """
        Generate the input prompt for the shell using the Bash PS1 environment variable
        Returns:
            str: The generated/formatted prompt
        """
        shell_format = self.computer.sessions[-1].env.get(
            "PS1") or "\\e[0;31m\\u\\e[0m@\\e[0;32m\\h\\e[0m:\\e[0;34m\\w\\\\e[0m\\$ "
        # Default shell prompt is <USERNAME>@<HOSTNAME>:<WORKING DIR><$/#>

        # \d   The date, in "Weekday Month Date" format (e.g., "Tue May 26").
        # \h   The hostname, up to the first .
        # \t   The time, in 24-hour HH:MM:SS format.
        # \T   The time, in 12-hour HH:MM:SS format.
        # \@   The time, in 12-hour am/pm format.
        # \u   The username of the current user.
        # \w   The current working directory.
        # \W   The basename of $PWD.
        # \$   If you are not root, inserts a "$"; if you are root, you get a "#"  (root uid = 0)
        # \e   An escape character (typically a color code).
        # \\   A backslash.

        prompt = shell_format
        prompt = prompt.replace("\\d", datetime.now().strftime("%a %B %d"))
        prompt = prompt.replace("\\h", self.computer.hostname)
        prompt = prompt.replace("\\t", datetime.now().strftime("%H:%M:%S"))
        prompt = prompt.replace("\\T", datetime.now().strftime("%I:%M:%S"))
        prompt = prompt.replace("\\@", datetime.now().strftime("%I:%M:%S %p"))
        prompt = prompt.replace("\\u", self.computer.find_user(uid=self.computer.get_uid()).data.username)
        prompt = prompt.replace("\\w", self.computer.sessions[-1].current_dir.pwd())
        prompt = prompt.replace("\\W", self.computer.sessions[-1].current_dir.pwd().split("/")[-1] or "/")
        prompt = prompt.replace("\\$", "#" if self.computer.get_uid() == 0 else "$")
        prompt = prompt.replace("\\\\", "\\")

        prompt = prompt.replace("\\e[0;31m", Fore.RED)
        prompt = prompt.replace("\\e[1;31m", Fore.LIGHTRED_EX)
        prompt = prompt.replace("\\e[0;32m", Fore.GREEN)
        prompt = prompt.replace("\\e[1;32m", Fore.LIGHTGREEN_EX)
        prompt = prompt.replace("\\e[0;33m", Fore.YELLOW)
        prompt = prompt.replace("\\e[1;33m", Fore.LIGHTYELLOW_EX)
        prompt = prompt.replace("\\e[0;34m", Fore.BLUE)
        prompt = prompt.replace("\\e[1;34m", Fore.LIGHTBLUE_EX)
        prompt = prompt.replace("\\e[0;35m", Fore.MAGENTA)
        prompt = prompt.replace("\\e[1;35m", Fore.LIGHTMAGENTA_EX)

        prompt = prompt.replace("\\e[41m", Back.RED)
        prompt = prompt.replace("\\e[42m", Back.GREEN)
        prompt = prompt.replace("\\e[43m", Back.YELLOW)
        prompt = prompt.replace("\\e[44m", Back.BLUE)
        prompt = prompt.replace("\\e[45m", Back.MAGENTA)
        prompt = prompt.replace("\\e[46m", Back.LIGHTBLUE_EX)

        # Remove color: \e[0m
        prompt = prompt.replace("\\e[0m", Style.RESET_ALL)

        return prompt

    def run_command(self, command: str, args: list, external_binary: bool, pipe: bool):
        """
        Determine how to run the given input, then, update the `Shell`'s prompt accordingly

        Args:
            command (str): The name of the command/binary to run
            args (list): The list of arguments passed by the user
            external_binary (bool): Weather or not we're running a standard system binary or an external binary
            pipe (bool): Weather or not we're going to pipe the command output to the input of another

        Returns:

        """
        if external_binary:
            pass
            # response = self.computer.run_binary(command, args, pipe)
        else:
            response = self.computer.run_command(command, args, pipe)
        self.prompt = self.generate_prompt()
        return response

    def try_run_command(self, command, args, pipe=False):
        external_binary = False
        # Try to flatten the list of args to make one list
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
            if result.success:
                return result.data
            else:
                return False
        except IndexError as e:
            print(e)
            print("error running command")

    def handle_command(self, command):
        """
        Handle the raw input from the user
        Parse out the args and special characters (|, >, >>, etc)
        Determine how to route input and output between commands

        Args:
            command (str): The raw input entered by the user

        Returns:

        """
        # Technically, the first element in our command should be the command name
        # And we can keep going through the
        command = command.split()
        # Filter!
        while "" in command:
            command.remove("")
        command_name = command[0]
        # Delete the command name from the command list (since we already have it)
        del command[0]

        # Easy cases if there are no special characters
        if "|" not in command and ">" not in command and ">>" not in command:
            # We only pass "command" because we already removed the initial command name (and saved it)
            self.try_run_command(command_name, command, False)
        else:
            prev_command_result = None
            while True:
                for arg in command:
                    # Check if the current arg is | > or >> (because we do something different here)
                    if arg in ["|", ">", ">>"]:
                        current_index = command.index(arg)
                        # Find the special character (|/>/>>) and decide what to do with it later
                        special_character = command[current_index]
                        break
                else:
                    # Run the last command and output
                    if len(command) == 0:
                        self.try_run_command(command_name, prev_command_result, False)
                    break

                current_args = command[0:current_index]

                if prev_command_result:
                    if type(prev_command_result) == list:
                        command_result = self.try_run_command(command_name,
                                                              current_args + prev_command_result, True)
                    else:
                        command_result = self.try_run_command(command_name,
                                                              current_args + [prev_command_result], True)
                else:
                    command_result = self.try_run_command(command_name, current_args, True)
                # Remove everything up to the current index (including the special character) (for the next cycle)
                del command[0:current_index + 1]

                # Don't even bother running if the command failed
                if command_result:
                    # If the special character is > (write output) or >> (append output)
                    # We expect the next character in the command to be the file to write/append to
                    if special_character in [">", ">>"]:
                        # We expect the next item after the > to be the file to write/append to
                        filename_to_write_to = command[0]
                        # We need to try to remove extra spaces from the given filename
                        filename_to_write_to = filename_to_write_to.replace(" ", "")

                        # Find the file that we should write the output to
                        find_response = self.computer.fs.find(filename_to_write_to)
                        if not find_response.success:
                            # This runs if the file doesn't exist (we need to create it)
                            find_response = self.computer.fs.find("/".join(filename_to_write_to.split("/")[:-1]))
                            if not find_response.success:
                                print(f"shell: no such file or directory: {filename_to_write_to}")
                            else:
                                # Create the new file
                                # We're using a syscall because it handles permissions (so we dont have to)
                                create_file_response = self.run_command("touch", [filename_to_write_to], False, True)
                                if not create_file_response.success:
                                    print(f"shell: unable to create file: {filename_to_write_to}")
                                    continue
                                else:
                                    file_to_write = self.computer.fs.find(filename_to_write_to).data
                        else:
                            file_to_write = find_response

                        message_to_write = command_result
                        if message_to_write.startswith('"') and message_to_write.endswith('"'):
                            message_to_write = message_to_write[1:-1]

                        # Since the rest of the code for the > and >> is the same up until this point
                        # We don't need to re-write it
                        if special_character == ">":
                            file_to_write.write(self.computer.get_uid(),
                                                message_to_write)
                        elif special_character == ">>":
                            file_to_write.append(self.computer.get_uid(),
                                                 message_to_write)

                        prev_command_result = None
                    # Pass the input of the previous command to the current command
                    elif special_character == "|":
                        prev_command_result = command_result
                        prev_command_result = prev_command_result.split()
                        command_name = command[0]
                        del command[0]

    def main(self):
        """
        Run the main input loop

        Returns:
            None
        """
        self.prompt = self.generate_prompt()
        while True:
            command = input(self.prompt)

            # We handle commands from left to right and && doesn't affect the previous commands, so we can start at &&
            if command:
                for cmd in command.split("&&"):
                    self.handle_command(cmd)

                self.prompt = self.generate_prompt()
