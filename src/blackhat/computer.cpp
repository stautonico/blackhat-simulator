#include <blackhat/computer.h>
#include <blackhat/fs/ext4.h>

#include <util/string.h>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stack>

Blackhat::Computer::Computer() {
    // Boot time
    this->_kinit();
}

void Blackhat::Computer::_kinit() {
    // The kernel's init function (not to be confused with userland init:
    // /sbin/init)
    bool has_filesystem = false;
    // this->_create_root_user();

    // TODO: Load the filesystem
    m_fs = Blackhat::Ext4::make_standard_fs();

    this->_new_computer_kinit();

    this->_post_fs_kinit();
}

void Blackhat::Computer::start() {
    // This function isn't automatically called because sometimes
    // we want a computer without starting it (like for testing)
    this->call_userland_init();

    // We should never reach this point, but if we did, init exited
    // so, we should panic and TODO: reboot?
    this->_kernel_panic("Init exited");
}

void Blackhat::Computer::_post_fs_kinit() {
    // TODO: Implement
}

void Blackhat::Computer::_new_computer_kinit() {
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

void Blackhat::Computer::_kernel_panic(std::string message) {
    std::cout << "Kernel panic - not syncing: " << message << std::endl;
    exit(1);
}
void Blackhat::Computer::call_userland_init() {
    // TODO: Load the /sbin/init from filesystem

    auto result = m_fs->read("/sbin/init");

    // Null value, aka doesn't exist, not empty string
    if (result == std::string(1, '\0')) {
        // Kernel panic message should be:
        // "Kernel panic on boot: run-init: /sbin/init: No such file or directory."
        _kernel_panic("/sbin/init: No such file or directory");
    }

    // TODO: Create a process
    Blackhat::Process proc(result, this);
    proc.set_cwd("/");
    proc.start_sync({});
}
void Blackhat::Computer::_create_fs_from_base(const std::string &basepath, const std::string current_path) {
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
int Blackhat::Computer::_exec(std::string path, std::vector<std::string> args) {
    auto result = m_fs->read(path);

    // Null value, aka doesn't exist, not empty string
    if (result == std::string(1, '\0')) {
        return -1;
    }

    Blackhat::Process proc(result, this);
    // TODO: Inherit parent cwd?
    proc.set_cwd("/");
    proc.start_sync(args);
    return 0;// TODO: Get the return value
}


std::string Blackhat::Computer::_read(std::string path) {
    auto result = m_fs->read(path);

    // Null value, aka doesn't exist, not empty string
    if (result == std::string(1, '\0')) {
        return result;
    }

    return result;
}
std::vector<std::string> Blackhat::Computer::_readdir(std::string path) {
    return m_fs->readdir(path);
}
