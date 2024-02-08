#include <blackhat/computer.h>
#include <blackhat/fs/basefs.h>
#include <blackhat/fs/ext4.h>
#include <blackhat/fs/file_descriptor.h>
#include <blackhat/fs/procfs.h>

#include <util/errno.h>
#include <util/string.h>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stack>
#include <sys/utsname.h>

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
        this->_create_root_user();

        if (!has_filesystem) {
            // TODO: Load the filesystem
            m_mount_points["/"] = Ext4::make_standard_fs("/", this);

            // Create some important files
            _create_system_files();
        }

        // Spin up our procfs
        m_mount_points["/proc"] = (BaseFS *) new Blackhat::ProcFS("/proc", this);


        this->_new_computer_kinit();

        this->_post_fs_kinit();
    }

    void Computer::_create_system_files() {
        // TODO: Unneeded when we have saving and loading
        m_mount_points["/"]->open("/etc/passwd", O::CREAT, 0);
    }

    void Computer::_create_root_user() {
        User rootuser(0, "root");
        rootuser.set_password("password");
        rootuser.set_home_dir("/root");
        m_users.insert({0, rootuser});
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
        m_mount_points["/"]->open("/tmp/unreadable", O::CREAT, 0);
        flush_users();// TODO: SYNC USERS WHEN WE HAVE SAVING, NOT FLUSH (??)
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

        // Create the /etc/os-release file
        // TODO: Should be a link to /usr/lib/os-release
        if (m_mount_points["/"]->open("/etc/os-release", O::CREAT, 0) == nullptr) {
            _kernel_panic("Failed to create /etc/os-release");
        }

        if (m_mount_points["/"]->write("/etc/os-release", "NAME=\"Blackhat Linux\"\nVERSION=\"0.0.0\"\nPRETTY_NAME=\"Blackhat Linux 0.0.0\"") < 0) {
            _kernel_panic("Failed to write to /etc/os-release");
        }
    }

    void Computer::_kernel_panic(std::string message) {
        std::cout << "Kernel panic - not syncing: " << message << std::endl;
        exit(1);
    }

    void Computer::call_userland_init() {
        // TODO: Load the /sbin/init from filesystem

        auto fd = m_mount_points["/"]->open("/sbin/init", O_RDONLY, 0);
        auto result = m_mount_points["/"]->read(fd);

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
                    if (!m_mount_points["/"]->exists(relative_path))
                        m_mount_points["/"]->open(relative_path, O::CREAT, 0);
                    dirs.push(entry.path().generic_string());// Generic string for win/lin compatability
                } else {
                    m_mount_points["/"]->open(relative_path, O::CREAT, 0);

                    m_mount_points["/"]->write(
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

    double Computer::get_boot_time() {
        std::chrono::steady_clock::time_point now = std::chrono::steady_clock::now();
        std::chrono::duration<double> duration = now - m_boot_time;
        double seconds = duration.count();

        return seconds;
    }

    void Computer::flush_users() {
        std::stringstream ss;

        for (auto const &[uid, user]: m_users) {
            ss << user.passwd_entry() << "\n";
        }

        // Remove the last newline
        auto towrite = ss.str();
        towrite.erase(towrite.size() - 1, 1);

        auto write_result = m_mount_points["/"]->write("/etc/passwd", towrite);

        if (write_result < 0) {
            _kernel_panic("failed to flush users to disk");
        }
    }

    std::string Computer::_read(std::string path) {
        // TODO: THIS IS BAD
        auto fd = m_mount_points["/"]->open(path, O_RDONLY, 0);
        auto result = m_mount_points["/"]->read(fd);

        // Null value, aka doesn't exist, not empty string
        if (result == std::string(1, '\0')) {
            return result;
        }

        return result;
    }

    std::vector<std::string> Computer::_readdir(std::string path) {

        // TODO: Make this a helper to find the proper file system
        // Start from the longest path, and keep popping off the last chunk until we find a match in our mappings
        std::vector<std::string> chunks;
        std::stringstream ss(path);
        std::string chunk;
        while (std::getline(ss, chunk, '/')) {
            chunks.push_back(chunk);
        }

        Blackhat::BaseFS *fs = nullptr;

        while (!chunks.empty()) {
            std::string subpath = "";
            for (const auto &c: chunks) {
                subpath += "/" + c;
            }
            if (subpath.empty()) {
                subpath = "/";
            }
            if (m_mount_points.find(subpath) != m_mount_points.end()) {
                fs = m_mount_points[subpath];
            }
            chunks.pop_back();
        }

        if (fs == nullptr) {
            // TODO: ERROR
            return {};
        }

        printf("%s\n", fs->get_mount_point().c_str());

        return fs->getdents(path);
    }

    BaseFS *Computer::_find_fs_from_path(std::string path) {
        // Start from the longest path, and keep popping off the last chunk until we find a match in our mappings
        std::vector<std::string> chunks;
        std::stringstream ss(path);
        std::string chunk;
        while (std::getline(ss, chunk, '/')) {
            chunks.push_back(chunk);
        }

        Blackhat::BaseFS *fs = nullptr;

        while (!chunks.empty()) {
            std::string subpath = "";
            for (const auto &c: chunks) {
                subpath += "/" + c;
            }
            if (subpath.empty()) {
                subpath = "/";
            }

            // Remove double "//"
            size_t pos = subpath.find_first_not_of('/');
            if (pos != std::string::npos && pos > 1) {
                subpath = "/" + subpath.substr(pos);
            }

            // TODO: Find out why calling `ls` looks for `/bin` in mount points
            //            printf("We're looking for %s in our mountpoints...\n", subpath.c_str());

            if (m_mount_points.find(subpath) != m_mount_points.end()) {
                fs = m_mount_points[subpath];
                break;
            }
            chunks.pop_back();
        }

        return fs;
    }

    int Computer::sys$open(std::string path, int flags, int mode, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto fs = _find_fs_from_path(path);

        if (fs == nullptr) {
            // TODO: Set error
            return -1;
        }


        auto stripped_path = strip_mount_point(path, fs->get_mount_point());

        // TODO: Implement permission checking (the fs's open function should do it)
        auto fd = fs->open(stripped_path, flags, mode);


        if (fd == nullptr) {
            // TODO: Set errno
            return -1;
        }

        // We want the full path, not the stripped path
        fd->m_path = path;


        // We have to get our open modes and check the permissions before we
        // create a file descriptor

        auto fd_num = caller_obj->get_fd_accumulator();

        fd->m_fd = fd_num;

        caller_obj->add_file_descriptor(fd);

        // TODO: Check our flags
        if (flags & O::APPEND) {
            fd->set_append(true);
        }

        return fd_num;// We have to do this bc add_file_descriptor increments the accumulator
    }

    int Computer::sys$close(int fd, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto fd_obj = caller_obj->get_file_descriptor(fd);

        if (fd_obj == nullptr) {
            caller_obj->set_errno(E::BADFD);
            return -1;
        }

        auto fs = _find_fs_from_path(fd_obj->get_path());

        // Let the filesystem clean up whatever it needs to
        fs->close(fd_obj);

        caller_obj->delete_file_descriptor(fd);

        return 0;
    }

    std::string Computer::sys$read(int fd, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto fd_obj = caller_obj->get_file_descriptor(fd);

        if (fd_obj == nullptr) {
            caller_obj->set_errno(E::BADF);
            return std::string(1, '\0');
        }

        // This should never fail since we can't open without the path existing
        // TODO: See what happens if this does fail
        auto fs = _find_fs_from_path(fd_obj->m_path);

        return fs->read(fd_obj);
    }

    int Computer::sys$write(int fd, std::string data, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto fd_obj = caller_obj->get_file_descriptor(fd);

        if (fd_obj == nullptr) {
            caller_obj->set_errno(E::BADF);
            return -1;
        }

        if (fd_obj->is_append_enabled())
            return fd_obj->append(data);
        else
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

        auto inode = m_mount_points["/"]->_find_inode(path);

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

        auto inode = m_mount_points["/"]->_find_inode(pathname);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        if (!inode->check_perm(Inode::Permission::EXECUTE, caller_obj)) {
            SETERRNO(E::PERM);
            return -1;
        }

        auto fd = m_mount_points["/"]->open(pathname, O_RDONLY, 0);
        auto file_content = m_mount_points["/"]->read(fd);

        //         Try to read the file content
        //        auto file_content = inode->read();

        // Null value, aka doesn't exist, not empty string
        if (file_content == std::string(1, '\0')) {
            caller_obj->set_errno(E::NOEXEC);
            return -1;
        }

        int uid;
        int gid;

        // TODO: Idk if this is correct, but we're just gonna use euid
        uid = caller_obj->get_euid();
        gid = caller_obj->get_egid();


        // TODO: Implement process spawner function
        Process *proc = new Process(file_content, this, uid, gid);
        proc->set_pid(m_pid_accumulator);
        m_processes[m_pid_accumulator] = proc;
        m_pid_accumulator++;

        proc->set_cwd(caller_obj->get_cwd());
        proc->set_env_from_parent(caller_obj->get_entire_environment());


        // TODO: Pass the environment
        proc->start_sync(argv);

        delete proc;
        return 0;// TODO: Get the return value
    }

    int Computer::sys$mkdir(std::string pathname, int mode, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_mount_points["/"]->_find_inode(pathname);

        if (inode != nullptr) {
            caller_obj->set_errno(E::EXIST);
            return -1;
        }

        // TODO: Set proper perms and owner
        if (m_mount_points["/"]->open(pathname, O::CREAT, 0) != nullptr) return true;

        return false;
    }

    int Computer::sys$rmdir(std::string pathname, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_mount_points["/"]->_find_inode(pathname);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        auto result = m_mount_points["/"]->rmdir(pathname);

        // TODO: Set errno
        if (result) return 0;
        else
            return -1;
    }

    int Computer::sys$unlink(std::string pathname, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_mount_points["/"]->_find_inode(pathname);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        auto result = m_mount_points["/"]->unlink(pathname);

        // TODO: Set errno

        return 0;
    }

    int Computer::sys$rename(std::string oldpath, std::string newpath, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto result = m_mount_points["/"]->rename(oldpath, newpath);
        // TODO: Check better
        // TODO: If the newpath is a directory, set errno to EISDIR

        if (!result) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        return 0;
    }

    int Computer::sys$setuid(int uid, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        // TODO: PROPER PERMISSION CHECKING!
        caller_obj->set_euid(uid);
        return 0;
    }

    int Computer::sys$setgid(int gid, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        // TODO: PROPER PERMISSION CHECKING!
        caller_obj->set_egid(gid);
        return 0;
    }

    int Computer::sys$getuid(int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        return caller_obj->get_uid();
    }

    int Computer::sys$geteuid(int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        return caller_obj->get_euid();
    }

    int Computer::sys$sethostname(std::string hostname, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        // TODO: Does this need any kind of validation?
        m_hostname = hostname;
        return 0;
    }

    std::vector<std::string> Computer::sys$uname(int caller) {
        std::vector<std::string> uname_output;


        struct utsname realUnameData;
        if (uname(&realUnameData) < 0)
            throw std::runtime_error("uname failed on line " + std::to_string(__LINE__ - 1));

        uname_output.emplace_back("Blackhat");// sysname (operating system name)
        uname_output.emplace_back(m_hostname);// nodename (hostname)
        uname_output.emplace_back("0.0.0");   // release (operating system release)
        uname_output.emplace_back("0.0.0");   // version (operating system version)
        uname_output.emplace_back("x86_64");  // Machine (hardware arch) TODO: Use real uname arch
        uname_output.emplace_back("");

        return uname_output;
    }

    int Computer::sys$link(std::string oldpath, std::string newpath, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        // Make sure both oldpath exists and newpath doesn't
        auto oldent = m_mount_points["/"]->_find_directory_entry(oldpath);

        if (oldent == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        auto newent = m_mount_points["/"]->_find_directory_entry(newpath);

        if (newent != nullptr) {
            caller_obj->set_errno(E::EXIST);
            return -1;
        }

        // Create a new directory entry that points to the same inode, but with newpath
        auto origInode = oldent->get_inode();

        auto split_path_components = split(newpath, '/');
        auto filename = split_path_components.back();
        split_path_components.pop_back();


        auto result = m_mount_points["/"]->add_inode_to_path(join(split_path_components, '/'), filename, origInode);
        origInode->increment_link_count();
        // TODO: Set errno?
        return result;
    }

    int Computer::sys$symlink(std::string oldpath, std::string newpath, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        // Make sure both oldpath exists and newpath doesn't
        auto oldent = m_mount_points["/"]->_find_directory_entry(oldpath);

        if (oldent == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return -1;
        }

        auto newent = m_mount_points["/"]->_find_directory_entry(newpath);

        if (newent != nullptr) {
            caller_obj->set_errno(E::EXIST);
            return -1;
        }

        auto new_inode_number = m_mount_points["/"]->open(newpath, O::CREAT, 0);

        if (new_inode_number == nullptr) {
            // TODO: Set some errno
            return -1;
        } else {
            auto new_inode = m_mount_points["/"]->_find_directory_entry(newpath)->get_inode();
            // Should never fail since we checked it above
            new_inode->make_symlink(oldpath);
        }


        return 0;
    }

    std::string Computer::sys$readlink(std::string pathname, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto inode = m_mount_points["/"]->_find_inode(pathname);

        if (inode == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return "";
        }

        if (!inode->is_symlink()) {
            caller_obj->set_errno(E::INVAL);
            return "";
        }

        return inode->get_linked_name();
    }


    std::vector<std::string> Computer::sys$stat(std::string pathname, int caller) {
        // TODO: Write a helper to validate the caller pid
        GETCALLER();

        auto dirent = m_mount_points["/"]->_find_directory_entry(pathname);

        if (dirent == nullptr) {
            caller_obj->set_errno(E::NOENT);
            return {};
        }

        auto inode = dirent->get_inode();

        // Shouldn't fail but check anyway
        if (inode == nullptr) {
            // TODO: EIO?
            caller_obj->set_errno(E::NOENT);
            return {};
        }

        std::vector<std::string> result;
        result.push_back("0");                                      // TODO: st_dev
        result.push_back(std::to_string(inode->get_inode_number()));// st_ino
        result.push_back(std::to_string(inode->get_mode()));        // st_mode TODO: format as octal
        result.push_back(std::to_string(inode->get_link_count()));  // st_nlink
        result.push_back(std::to_string(inode->get_uid()));         // st_uid
        result.push_back(std::to_string(inode->get_gid()));         // st_gid
        result.push_back("0");                                      // TODO: st_rdev
        result.push_back("0");                                      // TODO: st_size
        result.push_back("0");                                      // TODO: st_blksize
        result.push_back("0");                                      // TODO: st_blocks
        result.push_back("0");                                      // TODO: st_atim
        result.push_back("0");                                      // TODO: st_mtim
        result.push_back("0");                                      // TODO: st_ctim

        return result;
    }

    std::vector<std::string> Computer::sys$getdents(std::string pathname, int caller) {
        auto fs = _find_fs_from_path(pathname);

        if (fs == nullptr) {
            // TODO: Throw an error maybe? Errno maybe?
            return {};
        }

        return fs->getdents(strip_mount_point(pathname, fs->get_mount_point()));
    }

}// namespace Blackhat