import datetime
import unittest
from base64 import b32decode, b64decode
from hashlib import md5, sha1, sha256, sha512, sha384, sha224
from time import sleep
import unittest.mock
from getpass import getpass

from .setup_computers_universal import init
from ..helpers import Result, ResultMessages
from ..session import Session
from ..user import User


class TestIncludedBinaries(unittest.TestCase):
    """
    These test cases test the functionality of the binaries that are included with the system
    This is anything in the client/blackhat/bin folder (not including files in the installable folder)
    """

    def setUp(self) -> None:
        self.computer = init()

    def run_command(self, command, args):

        result = self.computer.run_command(command, args, True).data
        # This avoids "None type as no attribute strip"
        if not result:
            result = ""
        return result.strip("\n")

    def test_add_user(self):
        self.run_command("adduser", ["--version"])
        self.run_command("adduser", ["--help"])

        fail_bc_not_root_result = self.computer.run_command("adduser", ["testuser", "-p" "password", "-n"], True)
        expected_fail_bc_not_root_result = Result(success=False, message=ResultMessages.NOT_ALLOWED,
                                                  data="adduser: Only root can add new users!\n")

        self.assertEqual(fail_bc_not_root_result, expected_fail_bc_not_root_result)

        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))

        create_new_user_result = self.computer.run_command("adduser", ["testuser", "-p" "password", "-n"], True)
        expected_create_new_user_result = Result(success=True, message=None, data=None)
        create_duplicate_user_result = self.computer.run_command("adduser", ["testuser", "-p" "password", "-n"], True)
        expected_create_duplicate_user_result = Result(success=False, message=ResultMessages.ALREADY_EXISTS,
                                                       data="adduser: The user 'testuser' already exists.\n")

        self.assertEqual(create_new_user_result, expected_create_new_user_result)
        self.assertEqual(create_duplicate_user_result, expected_create_duplicate_user_result)

        # Now confirm that the user was actually added
        get_user_result = self.computer.get_user(username="testuser")
        expected_get_user_result = Result(success=True, message=None,
                                          data=User(1001, "testuser", md5("password".encode()).hexdigest()))
        self.assertEqual(get_user_result, expected_get_user_result)

    def test_base32(self):
        self.run_command("base32", ["--version"])
        self.run_command("base32", ["--help"])

        message = "Hello!"

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        base32_result = self.run_command("base32", ["file"]).split(" ")[1].strip("\n")
        self.assertEqual(b32decode(base32_result).decode().strip("\n"), message)

    def test_base64(self):
        self.run_command("base64", ["--version"])
        self.run_command("base64", ["--help"])

        message = "Hello!"

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        base64_result = self.run_command("base64", ["file"]).split(" ")[1]
        self.assertEqual(b64decode(base64_result).decode().strip("\n"), message)

    def test_cd(self):
        self.run_command("cd", ["--version"])
        self.run_command("cd", ["--help"])

        self.assertEqual(self.computer.sys_getcwd().pwd(), "/home/steve")
        self.run_command("cd", [".."])
        self.assertEqual(self.computer.sys_getcwd().pwd(), "/home")
        self.run_command("cd", ["..."])
        self.assertEqual(self.computer.sys_getcwd().pwd(), "/")
        self.run_command("cd", ["/etc/skel/Desktop"])
        self.assertEqual(self.computer.sys_getcwd().pwd(), "/etc/skel/Desktop")
        self.run_command("cd", ["~"])
        self.assertEqual(self.computer.sys_getcwd().pwd(), "/home/steve")

    def test_chown(self):
        self.run_command("chown", ["--version"])
        self.run_command("chown", ["--help"])

        self.run_command("touch", ["testfile"])

        self.assertEqual(self.computer.fs.find("/home/steve/testfile").data.owner, 1000)
        self.assertEqual(self.computer.fs.find("/home/steve/testfile").data.group_owner, 1000)

        self.run_command("chown", ["root:root", "testfile"])
        self.assertEqual(self.computer.fs.find("/home/steve/testfile").data.owner, 0)
        self.assertEqual(self.computer.fs.find("/home/steve/testfile").data.group_owner, 0)

    def test_clear(self):
        self.run_command("clear", ["--version"])
        self.run_command("clear", ["--help"])

        self.run_command("clear", [])

    def test_commands(self):
        self.run_command("commands", ["--version"])
        self.run_command("commands", ["--help"])

        commands_result = self.run_command("commands", [])
        self.assertIn("ls", commands_result)

        # Now lets remove ls from /bin (it shouldn't show up in commands)
        # We need root permissions
        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))
        move_result = self.computer.run_command("mv", ["/bin/ls", "/tmp"], True)
        self.assertTrue(move_result.success)

        commands_result = self.run_command("commands", [])
        self.assertNotIn("ls", commands_result)

    def test_date(self):
        self.run_command("date", ["--version"])
        self.run_command("date", ["--help"])

        date_result = self.run_command("date", [])

        local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        time_first = datetime.datetime.now().strftime('%a %b %d %I:%M:%S %p')
        time_second = datetime.datetime.now().strftime('%Y')

        expected_result = f"{time_first} {local_timezone} {time_second}"

        self.assertEqual(date_result, expected_result)

    def test_echo(self):
        self.run_command("echo", ["--version"])
        self.run_command("echo", ["--help"])

        echo_result = self.computer.run_command("echo", ["hello!"], True).data
        self.assertEqual(echo_result, "hello!\n")

        # Test -e flag
        echo_e_flag_result = self.computer.run_command("echo", ["-e", "hello\n\tworld!"], True).data
        self.assertEqual(echo_e_flag_result, "hello\n\tworld!\n")

        # Test -n flag
        echo_n_flag_result = self.computer.run_command("echo", ["-n", "hello world!\n"], True).data
        self.assertEqual(echo_n_flag_result, "hello world!\n")

    def test_env(self):
        self.run_command("env", ["--version"])
        self.run_command("env", ["--help"])

        env_result = self.run_command("env", [])
        print(f"ENVRESULT: {env_result}")
        self.assertEqual(env_result, "PATH=/usr/bin:/bin\nHOME=/home/steve\nUSER=steve")

    def test_export(self):
        self.run_command("export", ["--version"])
        self.run_command("export", ["--help"])

        # Lets get a baseline for the env before-hand
        env_result = self.run_command("printenv", [])
        self.assertEqual(env_result, "PATH=/usr/bin:/bin\nHOME=/home/steve\nUSER=steve")

        self.run_command("export", ["BASH=/bin/bash"])

        env_result = self.run_command("printenv", [])
        self.assertEqual(env_result, "PATH=/usr/bin:/bin\nHOME=/home/steve\nUSER=steve\nBASH=/bin/bash")

    def test_hostname(self):
        self.run_command("hostname", ["--version"])
        self.run_command("hostname", ["--help"])

        # We want to try to set the hostname without root permission (should fail)
        set_hostname_result = self.computer.run_command("hostname", ["localhost"], True)
        expected_set_hostname_result = Result(success=False,
                                              data="hostname: you must be root to change the host name")

        set_hostname_result.data = set_hostname_result.data.strip("\n")

        self.assertEqual(set_hostname_result, expected_set_hostname_result)

        # Make sure it failed
        get_hostname_result = self.run_command("hostname", [])

        self.assertNotEqual(get_hostname_result, "localhost")

        # Switch to root then change hostname
        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))

        self.run_command("hostname", ["localhost"])
        get_hostname_result = self.run_command("hostname", [])

        self.assertEqual(get_hostname_result, "localhost")

    def test_id(self):
        self.run_command("id", ["--version"])
        self.run_command("id", ["--help"])

        self_id_result = self.run_command("id", [])
        expected_self_id_result = "uid=1000(steve) gid=1000(steve) "
        self.assertEqual(self_id_result, expected_self_id_result)

        root_id_result = self.run_command("id", ["root"])
        root_id_by_uid_result = self.run_command("id", ["0"])
        expected_root_result = "uid=0(root) gid=0(root) "
        self.assertEqual(root_id_result, expected_root_result)
        self.assertEqual(root_id_by_uid_result, expected_root_result)

        # Check the flags
        id_result = self.run_command("id", ["-g"])
        self.assertEqual(id_result, "1000")

        id_result = self.run_command("id", ["-G"])
        self.assertEqual(id_result, "1000")

        id_result = self.run_command("id", ["-n"])
        self.assertEqual(id_result, "steve")

    def test_ls(self):
        import re
        self.run_command("ls", ["--version"])
        self.run_command("ls", ["--help"])

        # In the user's home directory, The files should be: Desktop Documents Downloads Music Pictures Public Templates Videos
        ls_result = self.computer.run_command("ls", ["--no-color"], True)
        expected_ls_result = Result(success=True, message=None,
                                    data="Desktop Documents Downloads Music Pictures Public Templates Videos ")

        ls_result.data = ls_result.data.strip("\n")

        color_filter = re.compile(r'\x1b[^m]*m')
        stripped_color = color_filter.sub('', ls_result.data)

        self.assertEqual(stripped_color, expected_ls_result.data)
        # Make sure .shellrc isn't there (as -a isn't specified)
        self.assertNotIn(".shellrc", ls_result.data)

        # Test -a flag (show hidden files)
        ls_result = self.run_command("ls", ["--no-color", "-a"])
        self.assertIn(".shellrc", ls_result)

        # Make sure -l flag works
        ls_result = self.run_command("ls", ["--no-color", "-l"])
        self.assertIn("steve", ls_result)

    def test_md5sum(self):
        self.run_command("md5sum", ["--version"])
        self.run_command("md5sum", ["--help"])

        message = "hello!"

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(md5((message + "\n").encode()).hexdigest(), self.run_command("md5sum", ["file"]))
        self.assertIn(md5(message.encode()).hexdigest(), self.run_command("md5sum", ["file", "-z"]))
        self.assertEqual(self.run_command("md5sum", ["file", "-z", "--tag"]),
                         f"MD5 (file) = {md5(message.encode()).hexdigest()}")

    def test_mv(self):
        self.run_command("mv", ["--version"])
        self.run_command("mv", ["--help"])

        # Make sure /bin/pwd exists
        find_pwd = self.computer.fs.find("/bin/pwd")
        self.assertTrue(find_pwd.success)

        # Make sure permissions work when moving
        self.assertFalse(self.computer.run_command("mv", ["/bin/pwd", "/tmp"], True).success)

        # Make sure /bin/pwd still exists
        find_pwd = self.computer.fs.find("/bin/pwd")
        self.assertTrue(find_pwd.success)

        # Make sure /tmp/pwd DOESN'T exists
        find_pwd = self.computer.fs.find("/tmp/pwd")
        self.assertFalse(find_pwd.success)

        # Root perms!
        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))

        self.run_command("mv", ["/bin/pwd", "/tmp"])

        # Make sure /bin/pwd DOESN'T exists
        find_pwd = self.computer.fs.find("/bin/pwd")
        self.assertFalse(find_pwd.success)

        # Make sure /tmp/pwd exists
        find_pwd = self.computer.fs.find("/tmp/pwd")
        self.assertTrue(find_pwd.success)

    def test_printenv(self):
        self.run_command("printenv", ["--version"])
        self.run_command("printenv", ["--help"])

        env_result = self.run_command("printenv", [])
        self.assertEqual(env_result, "PATH=/usr/bin:/bin\nHOME=/home/steve\nUSER=steve")

    def test_pwd(self):
        self.run_command("pwd", ["--version"])
        self.run_command("pwd", ["--help"])

        pwd_result = self.run_command("pwd", [])

        self.assertEqual("/home/steve", pwd_result)

    def test_sha1sum(self):
        self.run_command("sha1sum", ["--version"])
        self.run_command("sha1sum", ["--help"])

        message = "hello!"

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha1((message + "\n").encode()).hexdigest(), self.run_command("sha1sum", ["file"]))
        self.assertIn(sha1(message.encode()).hexdigest(), self.run_command("sha1sum", ["file", "-z"]))
        self.assertEqual(self.run_command("sha1sum", ["file", "-z", "--tag"]),
                         f"SHA1 (file) = {sha1(message.encode()).hexdigest()}")

    def test_sha224sum(self):
        self.run_command("sha224sum", ["--version"])
        self.run_command("sha224sum", ["--help"])

        message = "hello!"

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha224((message + "\n").encode()).hexdigest(),
                      self.run_command("sha224sum", ["file"]))
        self.assertIn(sha224(message.encode()).hexdigest(),
                      self.run_command("sha224sum", ["file", "-z"]))
        self.assertEqual(self.run_command("sha224sum", ["file", "-z", "--tag"]),
                         f"SHA224 (file) = {sha224(message.encode()).hexdigest()}")

    def test_sha256sum(self):
        self.run_command("sha256sum", ["--version"])
        self.run_command("sha256sum", ["--help"])

        message = "hello!"

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha256((message + "\n").encode()).hexdigest(),
                      self.run_command("sha256sum", ["file"]))
        self.assertIn(sha256(message.encode()).hexdigest(),
                      self.run_command("sha256sum", ["file", "-z"]))
        self.assertEqual(self.run_command("sha256sum", ["file", "-z", "--tag"]),
                         f"SHA256 (file) = {sha256(message.encode()).hexdigest()}")

    def test_sha384sum(self):
        self.run_command("sha384sum", ["--version"])
        self.run_command("sha384sum", ["--help"])

        message = "hello!"

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha384((message + "\n").encode()).hexdigest(),
                      self.run_command("sha384sum", ["file"]))
        self.assertIn(sha384(message.encode()).hexdigest(),
                      self.run_command("sha384sum", ["file", "-z"]))
        self.assertEqual(self.run_command("sha384sum", ["file", "-z", "--tag"]),
                         f"SHA384 (file) = {sha384(message.encode()).hexdigest()}")

    def test_sha512sum(self):
        self.run_command("sha512sum", ["--version"])
        self.run_command("sha512sum", ["--help"])

        message = "hello!"

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha512((message + "\n").encode()).hexdigest(),
                      self.run_command("sha512sum", ["file"]))
        self.assertIn(sha512(message.encode()).hexdigest(),
                      self.run_command("sha512sum", ["file", "-z"]))
        self.assertEqual(self.run_command("sha512sum", ["file", "-z", "--tag"]),
                         f"SHA512 (file) = {sha512(message.encode()).hexdigest()}")

    def test_sudo(self):
        # Sanity check
        sudo_result = self.run_command("id", [])

        self.assertIn("uid=1000(steve) gid=1000(steve)", sudo_result)

        # Add a new user to test later
        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))
        self.run_command("adduser", ["testuser", "-p" "password", "-n"])
        self.computer.sessions.pop()


        # We do both "getpass" and "fallback_getpass" because some terminals
        # (pycharm's one for example) uses the fallback function
        with unittest.mock.patch("getpass.getpass", return_value="password"):
            with unittest.mock.patch("getpass.fallback_getpass", return_value="password"):
                sudo_root_result = self.run_command("sudo", ["id"])
                self.assertIn("uid=0(root) gid=0(root)", sudo_root_result)

                other_user_result = self.run_command("sudo", ["-u", "testuser", "id"])
                self.assertIn("uid=1001(testuser) gid=1001(testuser)", other_user_result)

    def test_touch(self):
        self.run_command("touch", ["--version"])
        self.run_command("touch", ["--help"])

        touch_result = self.computer.run_command("touch", ["testfile"], True)
        expected_touch_result = Result(success=True)

        # We should double-check that the file exists in our home directory
        self.assertIn("testfile", self.run_command("ls", []))

        self.assertEqual(touch_result, expected_touch_result)

    def test_uname(self):
        self.run_command("uname", ["--version"])
        self.run_command("uname", ["--help"])

        # Test some misc uname configurations
        self.assertEqual(self.run_command("uname", [], ), "Linux")
        self.assertEqual(self.run_command("uname", ["-a"]),
                         f"Linux {self.computer.hostname} 1.1 v1 x86_64 Blackhat/Linux")
        self.assertEqual(self.run_command("uname", ["-mns"]),
                         f"Linux {self.computer.hostname} x86_64 ")
        self.assertEqual(self.run_command("uname", ["-op", "-i"]),
                         "unknown unknown Blackhat/Linux ")

    def test_unset(self):
        self.run_command("unset", ["--version"])
        self.run_command("unset", ["--help"])

        # Lets get a baseline for the env before-hand
        env_result = self.run_command("printenv", [])
        self.assertEqual(env_result, "PATH=/usr/bin:/bin\nHOME=/home/steve\nUSER=steve")

        self.run_command("export", ["BASH=/bin/bash"])

        env_result = self.run_command("printenv", [])
        self.assertEqual(env_result, "PATH=/usr/bin:/bin\nHOME=/home/steve\nUSER=steve\nBASH=/bin/bash")

        self.run_command("unset", ["BASH"])
        env_result = self.run_command("printenv", [])
        self.assertEqual(env_result, "PATH=/usr/bin:/bin\nHOME=/home/steve\nUSER=steve")

    def test_uptime(self):
        self.run_command("uptime", ["--version"])
        self.run_command("uptime", ["--help"])

        # Make sure it doesn't crash
        uptime_result = self.run_command("uptime", [])
        # TODO: See if there's a better way to fix this without wasting 5 seconds
        self.assertEqual(uptime_result, "uptime: 0:00:00")

        sleep(5)
        uptime_result = self.run_command("uptime", [])
        self.assertEqual(uptime_result, "uptime: 0:00:05")

        uptime_result = self.run_command("uptime", ["-p"])
        self.assertEqual(uptime_result, "up 0 minutes")

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime_result = self.run_command("uptime", ["-s"])

        # I'm going to strip out the seconds because different speed test runners can take different amount of times
        # to run

        now = ":".join(now.split(":")[:-1])
        uptime_result = ":".join(uptime_result.split(":")[:-1])

        # We have to check +1 or -1 minute because there is a possibility that it can be one minute behind
        minus_one_minute = uptime_result.split(":")
        minus_one_minute[1] = "{:02d}".format(int(minus_one_minute[1])-1)
        minus_one_minute = ":".join(minus_one_minute)

        plus_one_minute = uptime_result.split(":")
        plus_one_minute[1] = "{:02d}".format(int(plus_one_minute[1])+1)
        plus_one_minute = ":".join(plus_one_minute)

        self.assertIn(now, [minus_one_minute, uptime_result, plus_one_minute])

    def test_users(self):
        self.run_command("users", ["--version"])
        self.run_command("users", ["--help"])

        # One session = only one user
        users_result = self.run_command("users", [])
        self.assertEqual(users_result, "steve ")

        # Add new sessions then test
        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))
        users_result = self.run_command("users", [])
        self.assertEqual(users_result, "steve root ")

        self.computer.sessions.append(Session(1000, self.computer.fs.files, self.computer.sessions[-1].id + 1))
        users_result = self.run_command("users", [])
        self.assertEqual(users_result, "steve root steve ")

    def test_wc(self):
        self.run_command("wc", ["--version"])
        self.run_command("wc", ["--help"])

        message = "hello!"
        message_len = len(message + "\n")

        self.run_command("touch", ["file"])
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        wc_result = self.run_command("wc", ["file"])

        wc_split_results = wc_result.split(" ")
        while "" in wc_split_results:
            wc_split_results.remove("")

        total_new_line_count, total_word_count, total_byte_count = wc_split_results[0], wc_split_results[1], \
                                                                   wc_split_results[2]

        self.assertEqual(int(total_byte_count), message_len)
        self.assertEqual(int(total_new_line_count), 1)
        self.assertEqual(int(total_word_count), 1)

        wc_result = self.run_command("wc", ["file", "-c"])

        wc_split_results = wc_result.split(" ")
        while "" in wc_split_results:
            wc_split_results.remove("")

        total_byte_count = wc_split_results[0]

        self.assertEqual(int(total_byte_count), message_len)

        wc_result = self.run_command("wc", ["file", "-m"])

        wc_split_results = wc_result.split(" ")
        while "" in wc_split_results:
            wc_split_results.remove("")

        total_byte_count = wc_split_results[0]

        self.assertEqual(int(total_byte_count), message_len)

    def test_who(self):
        self.run_command("who", ["--version"])
        self.run_command("who", ["--help"])

        who_result = self.run_command("who", [])
        self.assertEqual(who_result, "steve\tpts/0")

    def test_whoami(self):
        self.run_command("whoami", ["--version"])
        self.run_command("whoami", ["--help"])

        whoami_result = self.run_command("whoami", [])

        self.assertEqual(whoami_result, "steve")


class TestInstallableBinaries(unittest.TestCase):
    """
    These test cases test the functionality of the binaries that are NOT included with the system
    (anything installable through apt)
    This is anything in the client/blackhat/bin/installable folder
    """

    def setUp(self) -> None:
        self.computer = init()
