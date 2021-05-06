import datetime
import unittest
from base64 import b32decode, b64decode
from hashlib import md5, sha1, sha256, sha512, sha384, sha224

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

    def test_add_user(self):
        self.computer.run_command("adduser", ["--version"], True)
        self.computer.run_command("adduser", ["--help"], True)

        fail_bc_not_root_result = self.computer.run_command("adduser", ["testuser", "-p" "password", "-n"], True)
        expected_fail_bc_not_root_result = Result(success=False, message=ResultMessages.NOT_ALLOWED, data="adduser: Only root can add new users!\n")

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
        self.computer.run_command("base32", ["--version"], True)
        self.computer.run_command("base32", ["--help"], True)

        message = "Hello!"

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        base32_result = self.computer.run_command("base32", ["file"], True).data.replace("\n", "").split(" ")[1]
        self.assertEqual(b32decode(base32_result).decode().strip("\n"), message)

    def test_base64(self):
        self.computer.run_command("base64", ["--version"], True)
        self.computer.run_command("base64", ["--help"], True)

        message = "Hello!"

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        base64_result = self.computer.run_command("base64", ["file"], True).data.replace("\n", "").split(" ")[1]
        self.assertEqual(b64decode(base64_result).decode().strip("\n"), message)

    def test_cd(self):
        self.computer.run_command("cd", ["--version"], True)
        self.computer.run_command("cd", ["--help"], True)

        self.assertEqual(self.computer.sys_getcwd().pwd(), "/home/steve")
        self.computer.run_command("cd", [".."], True)
        self.assertEqual(self.computer.sys_getcwd().pwd(), "/home")
        self.computer.run_command("cd", ["..."], True)
        self.assertEqual(self.computer.sys_getcwd().pwd(), "/")
        self.computer.run_command("cd", ["/etc/skel/Desktop"], True)
        self.assertEqual(self.computer.sys_getcwd().pwd(), "/etc/skel/Desktop")
        self.computer.run_command("cd", ["~"], True)
        self.assertEqual(self.computer.sys_getcwd().pwd(), "/home/steve")

    def test_chown(self):
        self.computer.run_command("chown", ["--version"], True)
        self.computer.run_command("chown", ["--help"], True)

        self.computer.run_command("touch", ["testfile"], True)

        self.assertEqual(self.computer.fs.find("/home/steve/testfile").data.owner, 1000)
        self.assertEqual(self.computer.fs.find("/home/steve/testfile").data.group_owner, 1000)

        self.computer.run_command("chown", ["root:root", "testfile"], True)
        self.assertEqual(self.computer.fs.find("/home/steve/testfile").data.owner, 0)
        self.assertEqual(self.computer.fs.find("/home/steve/testfile").data.group_owner, 0)

    def test_clear(self):
        self.computer.run_command("clear", ["--version"], True)
        self.computer.run_command("clear", ["--help"], True)

        self.computer.run_command("clear", [], True)

    def test_commands(self):
        self.computer.run_command("commands", ["--version"], True)
        self.computer.run_command("commands", ["--help"], True)

        commands_result = self.computer.run_command("commands", [], True).data.strip("\n")
        self.assertIn("ls", commands_result)

        # Now lets remove ls from /bin (it shouldn't show up in commands)
        # We need root permissions
        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))
        move_result = self.computer.run_command("mv", ["/bin/ls", "/tmp"], True)
        self.assertTrue(move_result.success)

        commands_result = self.computer.run_command("commands", [], True).data.strip("\n")
        self.assertNotIn("ls", commands_result)

    def test_date(self):
        self.computer.run_command("date", ["--version"], True)
        self.computer.run_command("date", ["--help"], True)

        date_result = self.computer.run_command("date", [], True)

        local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        time_first = datetime.datetime.now().strftime('%a %b %d %I:%M:%S %p')
        time_second = datetime.datetime.now().strftime('%Y')

        expected_result = f"{time_first} {local_timezone} {time_second}"

        self.assertEqual(date_result.data.strip("\n"), expected_result)

    def test_echo(self):
        self.computer.run_command("echo", ["--version"], True)
        self.computer.run_command("echo", ["--help"], True)

        echo_result = self.computer.run_command("echo", ["hello!"], True)
        self.assertEqual(echo_result.data, "hello!\n")

        # Test -e flag
        echo_e_flag_result = self.computer.run_command("echo", ["-e", "hello\n\tworld!"], True)
        self.assertEqual(echo_e_flag_result.data, "hello\n\tworld!\n")

        # Test -n flag
        echo_n_flag_result = self.computer.run_command("echo", ["-n", "hello world!\n"], True)
        self.assertEqual(echo_n_flag_result.data, "hello world!\n")

    def test_env(self):
        self.computer.run_command("env", ["--version"], True)
        self.computer.run_command("env", ["--help"], True)

        env_result = self.computer.run_command("env", [], True).data.strip("\n")
        self.assertEqual(env_result, "PATH=/usr/bin:/bin:\nHOME=/home/steve")

    def test_export(self):
        self.computer.run_command("export", ["--version"], True)
        self.computer.run_command("export", ["--help"], True)

        # Lets get a baseline for the env before-hand
        env_result = self.computer.run_command("printenv", [], True).data.strip("\n")
        self.assertEqual(env_result, "PATH=/usr/bin:/bin:\nHOME=/home/steve")

        self.computer.run_command("export", ["BASH=/bin/bash"], True)

        env_result = self.computer.run_command("printenv", [], True).data.strip("\n")
        self.assertEqual(env_result, "PATH=/usr/bin:/bin:\nHOME=/home/steve\nBASH=/bin/bash")

    def test_hostname(self):
        self.computer.run_command("hostname", ["--version"], True)
        self.computer.run_command("hostname", ["--help"], True)

        # We want to try to set the hostname without root permission (should fail)
        set_hostname_result = self.computer.run_command("hostname", ["localhost"], True)
        expected_set_hostname_result = Result(success=False,
                                                     data="hostname: you must be root to change the host name")

        set_hostname_result.data = set_hostname_result.data.strip("\n")

        self.assertEqual(set_hostname_result, expected_set_hostname_result)

        # Make sure it failed
        get_hostname_result = self.computer.run_command("hostname", [], True)

        self.assertNotEqual(get_hostname_result.data, "localhost")

        # Switch to root then change hostname
        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))

        self.computer.run_command("hostname", ["localhost"], True)
        get_hostname_result = self.computer.run_command("hostname", [], True)

        self.assertEqual(get_hostname_result.data.strip("\n"), "localhost")

    def test_id(self):
        self.computer.run_command("id", ["--version"], True)
        self.computer.run_command("id", ["--help"], True)

        self_id_result = self.computer.run_command("id", [], True).data.strip("\n")
        expected_self_id_result = "uid=1000(steve) gid=1000(steve) "
        self.assertEqual(self_id_result, expected_self_id_result)

        root_id_result = self.computer.run_command("id", ["root"], True).data.strip("\n")
        root_id_by_uid_result = self.computer.run_command("id", ["0"], True).data.strip("\n")
        expected_root_result = "uid=0(root) gid=0(root) "
        self.assertEqual(root_id_result, expected_root_result)
        self.assertEqual(root_id_by_uid_result, expected_root_result)

        # Check the flags
        id_result = self.computer.run_command("id", ["-g"], True).data.strip("\n")
        self.assertEqual(id_result, "1000")

        id_result = self.computer.run_command("id", ["-G"], True).data.strip("\n")
        self.assertEqual(id_result, "1000")

        id_result = self.computer.run_command("id", ["-n"], True).data.strip("\n")
        self.assertEqual(id_result, "steve")

    def test_ls(self):
        import re
        self.computer.run_command("ls", ["--version"], True)
        self.computer.run_command("ls", ["--help"], True)

        # In the user's home directory, The files should be: Desktop Documents Downloads Music Pictures Public Templates Videos
        ls_result = self.computer.run_command("ls", ["--no-color"], True)
        expected_ls_result = Result(success=True, message=None,
                                    data="Desktop Documents Downloads Music Pictures Public Templates Videos ")

        ls_result.data = ls_result.data.strip("\n")

        print(ls_result)
        print(expected_ls_result)

        color_filter = re.compile(r'\x1b[^m]*m')
        stripped_color = color_filter.sub('', ls_result.data)

        self.assertEqual(stripped_color, expected_ls_result.data)
        # Make sure .shellrc isn't there (as -a isn't specified)
        self.assertNotIn(".shellrc", ls_result.data)

        # Test -a flag (show hidden files)
        ls_result = self.computer.run_command("ls", ["--no-color", "-a"], True)
        self.assertIn(".shellrc", ls_result.data)

        # Make sure -l flag works
        ls_result = self.computer.run_command("ls", ["--no-color", "-l"], True)
        self.assertIn("steve", ls_result.data)

    def test_md5sum(self):
        self.computer.run_command("md5sum", ["--version"], True)
        self.computer.run_command("md5sum", ["--help"], True)

        message = "hello!"

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(md5((message + "\n").encode()).hexdigest(),
                      self.computer.run_command("md5sum", ["file"], True).data.strip("\n"))
        self.assertIn(md5(message.encode()).hexdigest(),
                      self.computer.run_command("md5sum", ["file", "-z"], True).data.strip("\n"))
        self.assertEqual(self.computer.run_command("md5sum", ["file", "-z", "--tag"], True).data.strip("\n"),
                         f"MD5 (file) = {md5(message.encode()).hexdigest()}")

    def test_mv(self):
        self.computer.run_command("mv", ["--version"], True)
        self.computer.run_command("mv", ["--help"], True)

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

        self.computer.run_command("mv", ["/bin/pwd", "/tmp"], True)

        # Make sure /bin/pwd DOESN'T exists
        find_pwd = self.computer.fs.find("/bin/pwd")
        self.assertFalse(find_pwd.success)

        # Make sure /tmp/pwd exists
        find_pwd = self.computer.fs.find("/tmp/pwd")
        self.assertTrue(find_pwd.success)

    def test_printenv(self):
        self.computer.run_command("printenv", ["--version"], True)
        self.computer.run_command("printenv", ["--help"], True)

        env_result = self.computer.run_command("printenv", [], True).data.strip("\n")
        self.assertEqual(env_result, "PATH=/usr/bin:/bin:\nHOME=/home/steve")

    def test_pwd(self):
        self.computer.run_command("pwd", ["--version"], True)
        self.computer.run_command("pwd", ["--help"], True)

        pwd_result = self.computer.run_command("pwd", [], True).data.strip("\n")

        self.assertEqual("/home/steve", pwd_result)

    def test_sha1sum(self):
        self.computer.run_command("sha1sum", ["--version"], True)
        self.computer.run_command("sha1sum", ["--help"], True)

        message = "hello!"

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha1((message + "\n").encode()).hexdigest(),
                      self.computer.run_command("sha1sum", ["file"], True).data.strip("\n"))
        self.assertIn(sha1(message.encode()).hexdigest(),
                      self.computer.run_command("sha1sum", ["file", "-z"], True).data.strip("\n"))
        self.assertEqual(self.computer.run_command("sha1sum", ["file", "-z", "--tag"], True).data.strip("\n"),
                         f"SHA1 (file) = {sha1(message.encode()).hexdigest()}")

    def test_sha224sum(self):
        self.computer.run_command("sha224sum", ["--version"], True)
        self.computer.run_command("sha224sum", ["--help"], True)

        message = "hello!"

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha224((message + "\n").encode()).hexdigest(),
                      self.computer.run_command("sha224sum", ["file"], True).data.strip("\n"))
        self.assertIn(sha224(message.encode()).hexdigest(),
                      self.computer.run_command("sha224sum", ["file", "-z"], True).data.strip("\n"))
        self.assertEqual(self.computer.run_command("sha224sum", ["file", "-z", "--tag"], True).data.strip("\n"),
                         f"SHA224 (file) = {sha224(message.encode()).hexdigest()}")

    def test_sha256sum(self):
        self.computer.run_command("sha256sum", ["--version"], True)
        self.computer.run_command("sha256sum", ["--help"], True)

        message = "hello!"

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha256((message + "\n").encode()).hexdigest(),
                      self.computer.run_command("sha256sum", ["file"], True).data.strip("\n"))
        self.assertIn(sha256(message.encode()).hexdigest(),
                      self.computer.run_command("sha256sum", ["file", "-z"], True).data.strip("\n"))
        self.assertEqual(self.computer.run_command("sha256sum", ["file", "-z", "--tag"], True).data.strip("\n"),
                         f"SHA256 (file) = {sha256(message.encode()).hexdigest()}")

    def test_sha384sum(self):
        self.computer.run_command("sha384sum", ["--version"], True)
        self.computer.run_command("sha384sum", ["--help"], True)

        message = "hello!"

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha384((message + "\n").encode()).hexdigest(),
                      self.computer.run_command("sha384sum", ["file"], True).data.strip("\n"))
        self.assertIn(sha384(message.encode()).hexdigest(),
                      self.computer.run_command("sha384sum", ["file", "-z"], True).data.strip("\n"))
        self.assertEqual(self.computer.run_command("sha384sum", ["file", "-z", "--tag"], True).data.strip("\n"),
                         f"SHA384 (file) = {sha384(message.encode()).hexdigest()}")

    def test_sha512sum(self):
        self.computer.run_command("sha512sum", ["--version"], True)
        self.computer.run_command("sha512sum", ["--help"], True)

        message = "hello!"

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        self.assertIn(sha512((message + "\n").encode()).hexdigest(),
                      self.computer.run_command("sha512sum", ["file"], True).data.strip("\n"))
        self.assertIn(sha512(message.encode()).hexdigest(),
                      self.computer.run_command("sha512sum", ["file", "-z"], True).data.strip("\n"))
        self.assertEqual(self.computer.run_command("sha512sum", ["file", "-z", "--tag"], True).data.strip("\n"),
                         f"SHA512 (file) = {sha512(message.encode()).hexdigest()}")

    def test_touch(self):
        self.computer.run_command("touch", ["--version"], True)
        self.computer.run_command("touch", ["--help"], True)

        touch_result = self.computer.run_command("touch", ["testfile"], True)
        expected_touch_result = Result(success=True)

        # We should double check that the file exists in our home directory
        self.assertIn("testfile", self.computer.run_command("ls", [], True).data)

        self.assertEqual(touch_result, expected_touch_result)

    def test_uname(self):
        self.computer.run_command("uname", ["--version"], True)
        self.computer.run_command("uname", ["--help"], True)

        # Test some misc uname configurations
        self.assertEqual(self.computer.run_command("uname", [], True).data.strip("\n"), "Linux")
        self.assertEqual(self.computer.run_command("uname", ["-a"], True).data.strip("\n"),
                         f"Linux {self.computer.hostname} 1.1 v1 x86_64 Blackhat/Linux")
        self.assertEqual(self.computer.run_command("uname", ["-mns"], True).data.strip("\n"),
                         f"Linux {self.computer.hostname} x86_64 ")
        self.assertEqual(self.computer.run_command("uname", ["-op", "-i"], True).data.strip("\n"),
                         "unknown unknown Blackhat/Linux ")

    def test_unset(self):
        self.computer.run_command("unset", ["--version"], True)
        self.computer.run_command("unset", ["--help"], True)

        # Lets get a baseline for the env before-hand
        env_result = self.computer.run_command("printenv", [], True).data.strip("\n")
        self.assertEqual(env_result, "PATH=/usr/bin:/bin:\nHOME=/home/steve")

        self.computer.run_command("export", ["BASH=/bin/bash"], True)

        env_result = self.computer.run_command("printenv", [], True).data.strip("\n")
        self.assertEqual(env_result, "PATH=/usr/bin:/bin:\nHOME=/home/steve\nBASH=/bin/bash")

        self.computer.run_command("unset", ["BASH"], True)
        env_result = self.computer.run_command("printenv", [], True).data.strip("\n")
        self.assertEqual(env_result, "PATH=/usr/bin:/bin:\nHOME=/home/steve")

    def test_uptime(self):
        self.computer.run_command("uptime", ["--version"], True)
        self.computer.run_command("uptime", ["--help"], True)

        # TODO: Add proper checking for flags
        # Make sure it doesn't crash
        uptime_result = self.computer.run_command("uptime", [], True).data.strip("\n")

    def test_users(self):
        self.computer.run_command("users", ["--version"], True)
        self.computer.run_command("users", ["--help"], True)

        # One session = only one user
        users_result = self.computer.run_command("users", [], True).data.strip("\n")
        self.assertEqual(users_result, "steve ")

        # Add new sessions then test
        self.computer.sessions.append(Session(0, self.computer.fs.files, self.computer.sessions[-1].id + 1))
        users_result = self.computer.run_command("users", [], True).data.strip("\n")
        self.assertEqual(users_result, "steve root ")

        self.computer.sessions.append(Session(1000, self.computer.fs.files, self.computer.sessions[-1].id + 1))
        users_result = self.computer.run_command("users", [], True).data.strip("\n")
        self.assertEqual(users_result, "steve root steve ")

    def test_wc(self):
        self.computer.run_command("wc", ["--version"], True)
        self.computer.run_command("wc", ["--help"], True)

        message = "hello!"
        message_len = len(message + "\n")

        self.computer.run_command("touch", ["file"], True)
        # We're writing with a new line to replicate what `echo hello! > file` would do
        self.computer.fs.find("/home/steve/file").data.write(message + "\n", self.computer)

        wc_result = self.computer.run_command("wc", ["file"], True).data.strip("\n")

        wc_split_results = wc_result.split(" ")
        while "" in wc_split_results:
            wc_split_results.remove("")

        total_new_line_count, total_word_count, total_byte_count = wc_split_results[0], wc_split_results[1], \
                                                                   wc_split_results[2]

        self.assertEqual(int(total_byte_count), message_len)
        self.assertEqual(int(total_new_line_count), 1)
        self.assertEqual(int(total_word_count), 1)

        wc_result = self.computer.run_command("wc", ["file", "-c"], True).data.strip("\n")

        wc_split_results = wc_result.split(" ")
        while "" in wc_split_results:
            wc_split_results.remove("")

        total_byte_count = wc_split_results[0]

        self.assertEqual(int(total_byte_count), message_len)

        wc_result = self.computer.run_command("wc", ["file", "-m"], True).data.strip("\n")

        wc_split_results = wc_result.split(" ")
        while "" in wc_split_results:
            wc_split_results.remove("")

        total_byte_count = wc_split_results[0]

        self.assertEqual(int(total_byte_count), message_len)

    def test_who(self):
        self.computer.run_command("who", ["--version"], True)
        self.computer.run_command("who", ["--help"], True)

        who_result = self.computer.run_command("who", [], True).data.strip("\n")
        self.assertEqual(who_result, "steve\tpts/0")

    def test_whoami(self):
        self.computer.run_command("whoami", ["--version"], True)
        self.computer.run_command("whoami", ["--help"], True)

        whoami_result = self.computer.run_command("whoami", [], True).data.strip("\n")

        self.assertEqual(whoami_result, "steve")


class TestInstallableBinaries(unittest.TestCase):
    """
    These test cases test the functionality of the binaries that are NOT included with the system
    (anything installable through apt)
    This is anything in the client/blackhat/bin/installable folder
    """

    def setUp(self) -> None:
        self.computer = init()

