import os
import pickle
from multiprocessing import Pipe
from typing import Union, Dict

from blackhat.fs import Filesystem
from blackhat.fs.filesystems.ext4 import Ext4, File, Directory
from blackhat.fs.mapping import FSMapping
from blackhat.process import Process
from blackhat.util.result import Result, ResultMessage
from blackhat.util.time import Timestamp


class Computer:
    """
    A class that represents the computer would be physically sitting in front of. (Should be a singleton instance)
    This class is a singleton, meaning there should only ever be one instance of it.
    """
    _instance = None

    def __init__(self):
        if Computer._instance is not None:
            raise Exception("Instance of Computer already exists, use Computer.get_instance() to access it.")
        else:
            Computer._instance = self

        self._BOOT_TIME = Timestamp()
        # self._users: Dict[int, User] = {} uid -> User
        # self._groups: Dict[int, Group] = {} gid -> Group

        self._hostname = "localhost"  # Fallback, will be overwritten by something else post-init

        # Ik that ICMP isn't really a service that runs on a port, but it's easier to do it this way
        # for the time being, at least for now. In reality, it's handled by the kernel's network stack,
        # but for the sake of simplicity, we'll just treat it as a service (on port 0, since port 0 is technically
        # an "invalid" port)
        # self._services: Dict[int, Service] = {}  # port -> Service
        self._fs_mappings: Dict[str, FSMapping] = {}  # path -> FSMapping (map a filesytem to a path)

        self._processes: Dict[int, Process] = {}  # pid -> Process
        self._process_pipes: Dict[int, Pipe] = {}  # pid -> Pipe

        self._pid_counter = 0

        # Set up our signal handler (for USR1 for syscall from process)
        # self.setup_signal_handler()

        # kinit, not to be confused with /bin/init (which is the first process, aka userland init)
        self._kinit()

    def _kinit(self):
        """
        Initialize the "kernel", and the computer object as a whole.
        """
        has_filesystem = False
        self._create_root_user()

        # Check if we have a saved filesystem ("disk")
        if os.path.exists("fs.bin"):
            with open("fs.bin", "rb") as f:
                filesystem = pickle.load(f)

            has_filesystem = True
        else:
            pass
            filesystem = Ext4.make_standard_filesystem()

            # TODO: Save our filesystem (but disable for testing)
            # with open("fs.bin", "wb") as f:
            #     pickle.dump(filesystem, f)

        self._add_fs_mapping("/", filesystem)

        if not has_filesystem:
            # Init our computer as if it was a fresh install (no filesystem)
            self._new_computer_init()

        # Some init steps that can only be done after the filesystem is loaded
        self._post_fs_init()

        # Spawn the root process (init)
        self.sys_execve("/sbin/init", [], {})

        # We should never reach this point, but if we did, init exited
        # so we should "kernel panic" and exit
        self._kernel_panic("init exited")

    def _post_fs_init(self):
        self.sync_hostname()

    def _new_computer_init(self):
        # Initialization steps when a saved computer isn't found (meaning these
        # steps are only done on a fresh install)
        self.flush_users()
        self.flush_groups()
        self.flush_hostname()

    def _create_root_user(self):
        # TODO: Implement
        pass
        # self._users[0] = User(0, "root")
        # # TODO: Set the root password to something random (or lock root user by default?)
        # self._users[0].set_password("password")

    def _kernel_panic(self, reason: str):
        print("Kernel panic - not syncing: " + reason)
        os._exit(1)  # This probably isn't the best way to do this, but it works for now
        # This force quits the program AND all sub-processes/threads

    # There are two types of functions, sync and flush
    # Sync is from filesystem to computer object, flush is from computer object to filesystem
    def sync_users(self):
        pass

    def flush_users(self):
        pass

    def sync_groups(self):
        pass

    def flush_groups(self):
        pass

    def sync_hostname(self):
        pass

    def flush_hostname(self):
        pass

    def _add_fs_mapping(self, path: str, filesystem: Filesystem):
        if path in self._fs_mappings:
            raise Exception(f"Mapping for path '{path}' already exists")

        self._fs_mappings[path] = FSMapping(path, filesystem)

    def _fs_find(self, path: str) -> Result[Union[File, Directory]]:
        """
        Find a mapping that matches the given path.
        :param path: The path to find a mapping for
        :return:
        """

        path = os.path.normpath(path)

        # Start from the longest path, and keep popping off the last chunk until we find a match in our mappings
        chunks = path.split("/")

        while len(chunks) > 0:
            subpath = "/".join(chunks)
            if subpath == "":
                subpath = "/"
            if subpath in self._fs_mappings:
                return self._fs_mappings[subpath].find(path)
            chunks.pop()

        return Result(False, message=ResultMessage.FS.PATH_NOT_FOUND)

    # Property functions (getters)
    @property
    def boot_time(self):
        return self._BOOT_TIME

    @staticmethod
    def get_instance():
        if Computer._instance is None:
            Computer()
        return Computer._instance


    # Syscalls
    def sys_execve(self, path: str, args: list, env: dict, ppid=None):
        # Find the file to execute
        find_file = self._fs_find(path)

        if find_file.success:
            # TODO: Pass the proper uid/gid
            # TODO: Pass env to process

            if ppid is None:
                cwd = self._fs_find("/").data
                parent = None
            else:
                cwd = self._processes[ppid].cwd
                parent = self._processes[ppid]


            process = Process.build_process(self._pid_counter, parent, 0, 0, path + " " + " ".join(args), cwd, find_file.data)

            # Make the two-way pipes for the process
            one, two = Pipe(True)
            self._process_pipes[process.pid] = one

            self._pid_counter += 1

            self._processes[process.pid] = process
            process.start(args, two, os.getpid())

            process.join()

            return process.exit_code
        else:
            print(f"Failed to find path: {path}")
            return 1