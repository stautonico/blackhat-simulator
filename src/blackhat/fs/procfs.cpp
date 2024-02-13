#include <blackhat/fs/procfs.h>
#include <util/errno.h>

namespace Blackhat {
    ProcFS::ProcFS(std::string mount_point, Computer *computer) : BaseFS("procfs") {
        m_mount_point = mount_point;
        m_computer = computer;
    }

    std::vector<std::string> ProcFS::getdents(std::string path) {
        // TODO: Improve this, but for now, its fine
        if (path == "/") {
            return {"uptime"};
        }

        return {};
    }

    FileDescriptor *ProcFS::open(std::string path, int flags, int mode) {
        // Make a fake inode to our data
        if (path == "/uptime") {
            auto inode = new Inode();
            inode->m_data = std::to_string(m_computer->get_boot_time());
            inode->m_link_count = 1;
            inode->m_mode = 0444 | IFREG;

            auto fd = new FileDescriptor(-1, path, inode);
            return fd;
        }

        return nullptr;
    }

    int ProcFS::close(Blackhat::FileDescriptor *fd) {
        // Unlike a regular filesystem, we need to delete our inode since its just temporary
        delete fd->m_inode;

        return 0;
    }


    std::string ProcFS::read(FileDescriptor *fd) {
        if (fd->get_path() == "/proc/uptime") {
            return std::to_string(m_computer->get_boot_time());
        }

        return "";
    }

    int ProcFS::unlink(std::string path) { return E::PERM; }
    int ProcFS::rename(std::string oldpath, std::string newpath) { return E::PERM; }
    int ProcFS::rmdir(std::string path) { return E::PERM; }
    int ProcFS::chown(std::string path, int uid, int gid) { return E::PERM; }
    int ProcFS::chmod(std::string path, int mode) { return E::PERM; }

}// namespace Blackhat