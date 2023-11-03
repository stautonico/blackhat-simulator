#include <blackhat/computer.h>
#include <blackhat/fs/ext4.h>
#include <blackhat/fs/file_descriptor.h>

#include <util/errno.h>
#include <util/string.h>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stack>

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

        // TODO: Load the filesystem
        m_fs = Ext4::make_standard_fs();

        this->_new_computer_kinit();

        this->_post_fs_kinit();
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
    }

    void Computer::_new_computer_kinit() {
        // The steps to take when the computer is new (no filesystem)
        // These setups usually relate to creating the base files in the fs
        // For now, this file simply follows the structure of the physical "base"
        // directory and copies it into the game, but maybe in the future,
        // this will change

        std::string path;

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
        Process proc(result, this);
        proc.set_cwd("/");
        proc.start_sync({});
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

    int Computer::sys$open(std::string path, int caller) {
        auto caller_obj = m_processes[caller];

        auto inode = m_fs->_find_inode(path);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        // TODO: Write a helper to validate the caller pid

        auto fd_num = caller_obj->get_fd_accumulator();

        FileDescriptor fd(fd_num, path, inode);
        caller_obj->add_file_descriptor(fd);

        return fd_num;// We have to do this bc add_file_descriptor increments the accumulator
    }

    std::string Computer::sys$read(int fd, int caller) {
        // TODO: Write a helper to validate the caller pid
        auto caller_obj = m_processes[caller];

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
        auto caller_obj = m_processes[caller];

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
        auto caller_obj = m_processes[caller];

        std::cout << "The cwd of pid: " << caller_obj->get_pid() << " is " << caller_obj->get_cwd() << std::endl;

        return caller_obj->get_cwd();
    }

    int Computer::sys$chdir(std::string path, int caller) {
        // TODO: Write a helper to validate the caller pid
        auto caller_obj = m_processes[caller];

        auto inode = m_fs->_find_inode(path);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        // TODO: Check for perms (EACCESS)
        // TODO: Check if inode is a directory (ENOTDIR)
        // TODO: Check name limit (ENAMETOOLONG)

        std::cout << "Setting the cwd for pid: " << caller_obj->get_pid() << " to " << path << std::endl;
        caller_obj->set_cwd(path);
        std::cout << "The result of the cwd of pid: " << caller_obj->get_pid() << " after changing is: " << caller_obj->get_cwd() << std::endl;

        return 0;
    }

    int Computer::sys$execve(std::string pathname, std::vector<std::string> argv, std::map<std::string, std::string> envp, int caller) {
        // TODO: Write a helper to validate the caller pid
        auto caller_obj = m_processes[caller];

        auto inode = m_fs->_find_inode(pathname);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        // TODO: Check if executable (EACCES)

        // Try to read the file content
        auto file_content = inode->read();

        // Null value, aka doesn't exist, not empty string
        if (file_content == std::string(1, '\0')) {
            caller_obj->set_errno(E::NOEXEC);
            return -1;
        }


        // TODO: Implement process spawner function
        Process *proc = new Process(file_content, this);
        proc->set_pid(m_pid_accumulator);
        m_processes[m_pid_accumulator] = proc;
        m_pid_accumulator++;

        // TODO: Come up with a proper solution for this
        if (caller_obj == nullptr) {// Temp solution for /sbin/init
            proc->set_cwd("/");
        } else {
            proc->set_cwd(caller_obj->get_cwd());
        }

        // TODO: Pass the environment
        proc->start_sync(argv);
        return 0;// TODO: Get the return value
    }

}// namespace Blackhat