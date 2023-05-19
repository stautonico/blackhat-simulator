import os


# Functions to set up an ext4 filesystem
def setup_bin(fs: "Ext4"):
    binary_path = os.path.join(os.getcwd(), "blackhat", "userland", "bin")

    for file in os.listdir(binary_path):
        # if file.endswith(".lua"):
        if file.endswith(".js"):
            # file = file.replace(".lua", "")
            file = file.replace(".js", "")
            if file in ["sudo", "su", "passwd"]:  # TODO: Add more files that need to be setuid
                mode = 0o4755
            else:
                mode = 0o755
            fs.create(os.path.join("/bin", file.replace(".js", "")), 0, 0, mode, False)
            with open(os.path.join(binary_path, file + ".js"), "r") as f:
                contents = f.read()

            fs.write(os.path.join("/bin", file.replace(".js", "")), contents)


def setup_etc(fs: "Ext4"):
    # TODO: Add functions to update the users and groups whenever the files are changed
    fs.create("/etc/passwd", 0, 0, 0o644, False)
    fs.create("/etc/group", 0, 0, 0o644, False)
    fs.create("/etc/shadow", 0, 0, 0o600, False)
    fs.create("/etc/hostname", 0, 0, 0o644, False)
    fs.create("/etc/hosts", 0, 0, 0o644, False)


def setup_home(fs: "Ext4"):
    pass


def setup_lib(fs: "Ext4"):
    pass


def setup_proc(fs: "Ext4"):
    pass


def setup_root(fs: "Ext4"):
    pass


def setup_run(fs: "Ext4"):
    pass

def setup_sbin(fs: "Ext4"):
    fs.create("/sbin/init", 0, 0, 0o755, False)

    # Read the contents of the init lua file
    # with open(os.path.join(os.getcwd(), "blackhat", "userland", "sbin", "init.lua"), "r") as f:
    with open(os.path.join(os.getcwd(), "blackhat", "userland", "sbin", "init.js"), "r") as f:
        contents = f.read()

    fs.write("/sbin/init", contents)


def setup_tmp(fs: "Ext4"):
    pass


def setup_usr(fs: "Ext4"):
    pass


def setup_var(fs: "Ext4"):
    pass
