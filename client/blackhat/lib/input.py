import argparse


class ArgParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        """
        Custom version of `argparse.ArgumentParser` that disable exiting when an error occurs

        This customer parser works exactly as the standard one does.
        The only difference is that `ArgParser.error_message` will exist if an error occurs.
        This variable should be checked for errors
        """
        super(ArgParser, self).__init__(*args, **kwargs)

        self.error_message = ''

    def error(self, message):
        """
        Override `error` method to prevent `ArgParser` from exiting on failure

        Args:
            message:

        Returns:

        """
        self.error_message = message

    def parse_args(self, *args, **kwargs):
        """
        Override `parse_args` method to prevent `ArgParser` from exiting on failure

        Args:
            *args:
            **kwargs:

        Returns:

        """
        # catch SystemExit exception to prevent closing the application
        result = None
        try:
            result = super().parse_args(*args, **kwargs)
        except SystemExit:
            pass
        return result
