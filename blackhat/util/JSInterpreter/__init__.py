import traceback

import js2py
from js2py import EvalJs
import os
from time import sleep

js2py.disable_pyimport()


class JSInterpreter:
    def __init__(self, process):
        self._process = process

        self._loaded_modules = []

        self.ctx = EvalJs(self._make_context())

    def _make_context(self):
        return {
            "require": self.builtin_require
        }

    def builtin_require(self, module):
        if module in self._loaded_modules:
            return None

        # TODO: Make this load from the filesystem
        if module == "unistd":
            with open("blackhat/util/JSInterpreter/unistd.js", "r") as f:
                code = f.read()
        elif module == "stdio":
            with open("blackhat/util/JSInterpreter/stdio.js", "r") as f:
                code = f.read()

        self._loaded_modules.append(module)
        return self.ctx.execute(code)

    def execute_main(self, code: str, args: list):
        try:
            # TODO: Find a way to validate the code before executing it
            self.ctx.execute(code)
            return self.ctx.main(args, args)
        except Exception as e:
            print("Failed to run main function:")
            traceback.print_exc()
            return 139
