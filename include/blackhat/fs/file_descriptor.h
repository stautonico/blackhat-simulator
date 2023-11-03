#pragma once

#include <string>

// Forward declaration
namespace Blackhat {
    class Inode;
}

#include <blackhat/fs/ext4.h>

// https://www.oreilly.com/library/view/linux-device-drivers/0596000081/ch03s04.html

namespace Blackhat {

    enum FDModes {
        FMODE_READ = 1 << 0,
        FMODE_WRITE = 1 << 1
    };

    enum FDFlags {
        O_RDONLY     = 0,        // Open for read-only
        O_WRONLY     = 1,        // Open for write-only
        O_RDWR       = 2,        // Open for read and write
        O_CREAT      = 0100,     // Create if it does not exist
        O_EXCL       = 0200,
        O_NOCTTY     = 0400,
        O_TRUNC      = 01000,    // Truncate to zero length on opening
        O_APPEND     = 02000,    // Append on each write
        O_NONBLOCK   = 04000,    // Open in non-blocking mode
        O_DSYNC      = 010000,
        O_FASYNC     = 020000,
        O_LARGEFILE  = 0100000, // Enable "large file" support
        O_DIRECTORY  = 0200000,  // Must be a directory
        O_NOFOLLOW   = 0400000,
        O_NOATIME    = 01000000, // Do not update access time
        O_CLOEXEC    = 02000000  // Close the file descriptor on exec
    };


    class FileDescriptor {
    public:
        FileDescriptor(int fd, std::string path, Inode* inode);

        int get_fd() {return m_fd;}

        std::string read();
        int write(std::string data);

    private:
        int m_fd;
        std::string m_path;
        Inode *m_inode;

        int f_mode;
        int f_pos;
        int f_flags;
        // TODO: Maybe include f_pid (the pid that this fd belongs to?)
        //       Might be unnecessary?
    };
};