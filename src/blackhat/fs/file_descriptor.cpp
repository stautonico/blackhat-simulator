#include <blackhat/fs/file_descriptor.h>

namespace Blackhat {
    FileDescriptor::FileDescriptor(int fd, std::string path, Blackhat::Inode *inode) {
        m_fd = fd;
        m_path = path;
        m_inode = inode;

        // TODO: Set mode and flags in separate functions?
    }

    std::string FileDescriptor::read() {
        return m_inode->read();
    }

    int FileDescriptor::write(std::string data) {
        return m_inode->write(data);
    }
}// namespace Blackhat