import argparse


class ArgParser(argparse.ArgumentParser):
    """
    Custom version of `argparse.ArgumentParser` that disable exiting when an error occurs

    This customer parser works exactly as the standard one does.
    The only difference is that `ArgParser.error_message` will exist if an error occurs.
    This variable should be checked for errors
    """
    def __init__(self, *args, **kwargs):
        super(ArgParser, self).__init__(*args, **kwargs)

        self.error_message = ''

    def error(self, message):
        self.error_message = message

    def parse_args(self, *args, **kwargs):
        # catch SystemExit exception to prevent closing the application
        result = None
        try:
            result = super().parse_args(*args, **kwargs)
        except SystemExit:
            pass
        return result
