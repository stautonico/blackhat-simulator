import enum
import os
import signal
from threading import Thread
import multiprocessing
from typing import List, Optional

import rpyc

from blackhat.fs.filesystems.ext4 import File
import blackhat
from blackhat.util.JSInterpreter import JSInterpreter


class ProcessState(enum.Enum):
    TASK_RUNNING = 0
    TASK_INTERRUPTIBLE = 1
    TASK_UNINTERRUPTIBLE = 2
    TASK_STOPPED = 4
    TASK_TRACED = 8
    EXIT_DEAD = 16
    EXIT_ZOMBIE = 32
    EXIT_TRACE = 48
    TASK_DEAD = 64
    TASK_WAKEKILL = 128
    TASK_WAKING = 256
    TASK_PARKED = 512
    TASK_NOLOAD = 1024
    TASK_STATE_MAX = 2048


class Process:
    # Intended to be used through the "ProcessBuilder" function
    def __init__(self):
        self._pid: int = None
        self._ppid: int = None
        self._state: ProcessState = None
        self._exit_code: int = None
        self._parent: Process = None
        self._children: List[Process] = []

        self._uid: int = 0  # user identifier
        self._euid: int = None  # effective UID used for privilege checks
        self._suid: int = None  # saved UID used to support switching permission
        self._fsuid: int = None  # UID used for filesystem access checks (used by NFS for example)

        self._gid: int = None  # group identifier
        self._egid: int = None  # effective GID used for privilege checks
        self._sgid: int = None  # saved GID used to support switching permission
        self._fgid: int = None  # GID used for filesystem access checks

        # ?
        self._name: str = None

        # TODO: Maybe implement threads
        self._threads: List[Process] = []

        self._cmdline: str = None  # <command> <args> used to start the process

        # TODO: Typehint this
        self._cwd = None  # current working directory
        self._exe: File = None  # "Pointer" to the file that is executed

        self._running = False

        # TODO: Setup js interpreter
        self._interpreter = JSInterpreter(self)
        self._code = None  # The executable code (contained in the "exe" file)

        self._pipe = None  # Duplex pipe to communicate with the "root" process (the main game process)

        self._root_pid = None # The pid of the "root" process (the main game process)

        # TODO: Setup some file descriptors (stdin, stdout, stderr, ...)

    def set_exit_code(self, exit_code):
        if exit_code > 255 or exit_code < 0:
            # AND the code with 0xFF to get the last 8 bits
            exit_code &= 0xFF  # 0xFF = 11111111 (255)

        self._exit_code = exit_code

    @staticmethod
    def build_process(pid: int, parent: Optional["Process"], uid: int, gid: int, cmdline: str, cwd, exe: File):
        # TODO: Typehint cwd
        process = Process()
        process._pid = pid
        if parent is not None:
            process._ppid = parent._pid
        else:
            process._ppid = -1
        process._parent = parent

        process._uid = uid
        process._euid = uid
        process._suid = uid
        process._fsuid = uid
        process._gid = gid
        process._egid = gid
        process._sgid = gid
        process._fgid = gid

        process._cmdline = cmdline
        process._cwd = cwd
        process._exe = exe

        # This should never fail (bc we can't execute a file that doesn't exist or that we can't read)
        # Force read because we don't need read permissions to execute a file (only execute permissions)
        process._code = exe._data

        return process

    def _run(self, args: List[str]):
        # TODO: Setup signal handler

        self._running = True

        self._exit_code = self._interpreter.execute_main(self._code, args) or 139

    def start(self, args: List[str], pipe, root_pid):
        self._pipe = pipe

        self._root_pid = root_pid

        process = multiprocessing.Process(target=self._run, args=(args,))

        self._threads.append(process)

        process.start()

    def join(self):
        for thread in self._threads:
            thread.join()

        return self._exit_code

    @property
    def pid(self):
        return self._pid

    @property
    def cwd(self):
        return self._cwd

    @property
    def exit_code(self):
        return self._exit_code
