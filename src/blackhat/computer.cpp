#include <blackhat/computer.h>
#include <blackhat/fs/ext4.h>
#include <blackhat/fs/file_descriptor.h>

#include <util/errno.h>
#include <util/string.h>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stack>

#define GETCALLER() auto caller_obj = m_processes[caller]
#define SETERRNO(errno) caller_obj->set_errno(errno)

namespace Blackhat {
    Computer::Computer() {
        // Boot time
        this->_kinit();
    }

    void Computer::_kinit() {
        // The kernel's init function (not to be confused with userland init:
        // /sbin/init)
        bool has_filesystem = false;
        // this->_create_root_user();

        if (!has_filesystem) {
            // TODO: Load the filesystem
            m_fs = Ext4::make_standard_fs();

            // Create some important files
            _create_system_files();
        }


        this->_new_computer_kinit();

        this->_post_fs_kinit();
    }

    void Computer::_create_system_files() {
        m_fs->create("/etc/passwd", 0, 0, 0644);
    }

    void Computer::start() {
        // This function isn't automatically called because sometimes
        // we want a computer without starting it (like for testing)
        this->call_userland_init();

        // We should never reach this point, but if we did, init exited
        // so, we should panic and TODO: reboot?
        this->_kernel_panic("Init exited");
    }

    void Computer::_post_fs_kinit() {
        // TODO: Implement
        // Create a test tmp file that is unreadable to anyone but root
        m_fs->create("/tmp/unreadable", 0, 0, 0);
    }

    void Computer::_new_computer_kinit() {
        // The steps to take when the computer is new (no filesystem)
        // These setups usually relate to creating the base files in the fs
        // For now, this file simply follows the structure of the physical "base"
        // directory and copies it into the game, but maybe in the future,
        // this will change

        std::string path;

        // TODO: Fix this temporary code
        if (std::filesystem::exists("base"))
            path = "base";
        else if (std::filesystem::exists("../base"))
            path = "../base";
        else if (std::filesystem::exists("../../base"))
            path = "../../base";
        else
            _kernel_panic("No base directory found: Cannot initialize filesystem");

        _create_fs_from_base(path, path);
    }

    void Computer::_kernel_panic(std::string message) {
        std::cout << "Kernel panic - not syncing: " << message << std::endl;
        exit(1);
    }

    void Computer::call_userland_init() {
        // TODO: Load the /sbin/init from filesystem

        auto result = m_fs->read("/sbin/init");

        // Null value, aka doesn't exist, not empty string
        if (result == std::string(1, '\0')) {
            // Kernel panic message should be:
            // "Kernel panic on boot: run-init: /sbin/init: No such file or directory."
            _kernel_panic("/sbin/init: No such file or directory");
        }

        // TODO: Create a process
        Process *proc = new Process(result, this, 0, 0);
        proc->set_cwd("/");
        proc->set_pid(1);
        m_processes[1] = proc;
        proc->start_sync({});
    }

    void Computer::_create_fs_from_base(const std::string &basepath, const std::string current_path) {
        std::stack<std::string> dirs;
        dirs.push(current_path);

        while (!dirs.empty()) {
            const std::string dir_path = dirs.top();
            dirs.pop();

            for (const auto &entry: std::filesystem::directory_iterator(dir_path)) {
                std::string relative_path =
                        entry.path().generic_string().substr(basepath.length());
                if (std::filesystem::is_directory(entry.status())) {
                    // Check if it already exists
                    if (!m_fs->exists(relative_path))
                        m_fs->create(relative_path, 0, 0, 0644);
                    dirs.push(entry.path().generic_string());// Generic string for win/lin compatability
                } else {
                    m_fs->create(relative_path, 0, 0, 0755);

                    m_fs->write(
                            erase(entry.path().generic_string(), basepath),
                            std::string(
                                    std::istreambuf_iterator<char>(
                                            std::ifstream(entry.path().generic_string(), std::ios::binary)
                                                    .rdbuf()),
                                    std::istreambuf_iterator<char>()));
                }
            }
        }
    }

    std::string Computer::_read(std::string path) {
        auto result = m_fs->read(path);

        // Null value, aka doesn't exist, not empty string
        if (result == std::string(1, '\0')) {
            return result;
        }

        return result;
    }

    std::vector<std::string> Computer::_readdir(std::string path) {
        return m_fs->readdir(path);
    }

    int Computer::sys$open(std::string path, int flags, int mode, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        // We have to get our open modes and check the permissions before we
        // create a file descriptor

        // TODO: Implement permissions for this
        if (flags & O::CREAT) {
            // TODO: Set mode and uid/gid and stuff
            auto result = m_fs->create(path, 0, 0, mode);
            if (!result) return -1;
        }

        auto inode = m_fs->_find_inode(path);

        // ENOENT check comes first
        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        // Then permission checks
        if (flags & O::RDWR) {
            // Check if we have read and write permissions
            if (!inode->check_perm(Inode::Permission::READ, caller_obj) ||
                !inode->check_perm(Inode::Permission::WRITE, caller_obj)) {
                caller_obj->set_errno(E::PERM);
                return -1;
            }
        } else if (flags & O::WRONLY) {
            if (!inode->check_perm(Inode::Permission::WRITE, caller_obj)) {
                caller_obj->set_errno(E::PERM);
                return -1;
            }
        } else {
            // We can't check flags & O::RDONLY since RDONLY = 0
            if (!inode->check_perm(Inode::Permission::READ, caller_obj)) {
                caller_obj->set_errno(E::PERM);
                return -1;
            }
        }

        // Now, in theory, we should have the correct permissions, so we can just make a fd


        auto fd_num = caller_obj->get_fd_accumulator();

        FileDescriptor fd(fd_num, path, inode);
        caller_obj->add_file_descriptor(fd);

        return fd_num;// We have to do this bc add_file_descriptor increments the accumulator
    }

    std::string Computer::sys$read(int fd, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto fd_obj = caller_obj->get_file_descriptor(fd);

        if (fd_obj == nullptr) {
            caller_obj->set_errno(E::BADF);
            return std::string(1, '\0');
        }

        // TODO: Permission check
        return fd_obj->read();
    }

    int Computer::sys$write(int fd, std::string data, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto fd_obj = caller_obj->get_file_descriptor(fd);

        if (fd_obj == nullptr) {
            caller_obj->set_errno(E::BADF);
            return -1;
        }

        // TODO: Permission check
        return fd_obj->write(data);
    }

    std::string Computer::sys$getcwd(int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        return caller_obj->get_cwd();
    }

    int Computer::sys$chdir(std::string path, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_fs->_find_inode(path);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        // TODO: Check for perms (EACCESS)
        // TODO: Check if inode is a directory (ENOTDIR)
        // TODO: Check name limit (ENAMETOOLONG)

        caller_obj->set_cwd(path);

        return 0;
    }

    int
    Computer::sys$execve(std::string pathname, std::vector<std::string> argv, std::map<std::string, std::string> envp,
                         int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_fs->_find_inode(pathname);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        if (!inode->check_perm(Inode::Permission::EXECUTE, caller_obj)) {
            SETERRNO(E::PERM);
            return -1;
        }

        // Try to read the file content
        auto file_content = inode->read();

        // Null value, aka doesn't exist, not empty string
        if (file_content == std::string(1, '\0')) {
            caller_obj->set_errno(E::NOEXEC);
            return -1;
        }

        int uid;
        int gid;

        uid = caller_obj->get_uid();
        gid = caller_obj->get_gid();


        // TODO: Implement process spawner function
        Process *proc = new Process(file_content, this, uid, gid);
        proc->set_pid(m_pid_accumulator);
        m_processes[m_pid_accumulator] = proc;
        m_pid_accumulator++;

        proc->set_cwd(caller_obj->get_cwd());


        // TODO: Pass the environment
        proc->start_sync(argv);
        return 0;// TODO: Get the return value
    }

    int Computer::sys$mkdir(std::string pathname, int mode, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_fs->_find_inode(pathname);

        if (inode != nullptr) {
            caller_obj->set_errno(E::EXIST);
            return -1;
        }

        // TODO: Set proper perms and owner
        if (m_fs->create(pathname, 0, 0, mode)) return true;

        return false;
    }

    int Computer::sys$rmdir(std::string pathname, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_fs->_find_inode(pathname);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        auto result = m_fs->rmdir(pathname);

        // TODO: Set errno
        if (result) return 0;
        else
            return -1;
    }

    int Computer::sys$unlink(std::string pathname, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_fs->_find_inode(pathname);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        auto result = m_fs->unlink(pathname);

        // TODO: Set errno

        return 0;
    }

    int Computer::sys$rename(std::string oldpath, std::string newpath, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto result = m_fs->rename(oldpath, newpath);
        // TODO: Check better
        // TODO: If the newpath is a directory, set errno to EISDIR

        if (!result) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        return 0;
    }

}// namespace Blackhat