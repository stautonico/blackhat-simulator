#pragma once

#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <sstream>

#define NOT_IMPL()                                     \
    {                                                  \
        std::stringstream ss;                          \
        ss << __FUNCTION__;                            \
        ss << "() is not implemented in filesystem '"; \
        ss << m_fs_name;                               \
        ss << "'!";                                    \
        throw std::runtime_error(ss.str());            \
    }

namespace Blackhat {
    class DirectoryEntry;
    class Computer;
}// namespace Blackhat


#include <blackhat/fs/file_descriptor.h>

namespace Blackhat {
    enum S : unsigned int {
        IXOTH = 0x1,
        IWOTH = 0x2,
        IROTH = 0x4,
        IXGRP = 0x8,
        IWGRP = 0x10,
        IRGRP = 0x20,
        IXUSR = 0x40,
        IWUSR = 0x80,
        IRUSR = 0x100,
        ISVTX = 0x200,
        ISGID = 0x400,
        ISUID = 0x800,
        // Mutually exclusive
        IFIFO = 0x1000,
        IFCHR = 0x2000,
        IFDIR = 0x4000,
        IFBLK = 0x6000,
        IFREG = 0x8000,
        IFLNK = 0xA000,
        IFSOCK = 0xC000
    };

    inline bool ISFIFO(int mode) {
        return mode & S::IFIFO == S::IFIFO;
    }

    inline bool ISCHR(int mode) {
        return mode & S::IFCHR == S::IFCHR;
    }

    inline bool ISDIR(int mode) {
        return mode & S::IFDIR == S::IFDIR;
    }

    inline bool ISBLK(int mode) {
        return mode & S::IFBLK == S::IFBLK;
    }

    inline bool ISREG(int mode) {
        return mode & S::IFREG == S::IFREG;
    }

    inline bool ISLNK(int mode) {
        return mode & S::IFLNK == S::IFLNK;
    }

    inline bool ISSOCK(int mode) {
        return mode & S::IFSOCK == S::IFSOCK;
    }


    enum O : unsigned int {
        APPEND = 00002000,
        ASYNC = 020000,
        CLOEXEC = 02000000,
        CREAT = 00000100,
        DIRECT = 00040000,
        DIRECTORY = 00200000,
        DSYNC = 00010000,
        EXCL = 00000200,
        LARGEFILE = 00100000,
        NOATIME = 01000000,
        NOCTTY = 00000400,
        NOFOLLOW = 00400000,
        NONBLOCK = 00004000,
        PATH = 010000000,
        SYNC = 00010000,
        TMPFILE = 020000000,
        TRUNC = 00001000,

        RDONLY = 00000000,
        WRONLY = 00000001,
        RDWR = 00000002,
    };

    class BaseFS {
    public:
        BaseFS(std::string fs_name) {
            m_fs_name = fs_name;
        };

        ~BaseFS(){};

        inline std::string get_mount_point() {
            return m_mount_point;
        }

        // https://www.cs.hmc.edu/~geoff/classes/hmc.cs135.201001/homework/fuse/fuse_doc.html
        virtual int getattr(std::string path){NOT_IMPL()};// the 'stat' command basically // TODO: set the return value properly
        virtual void readlink(){NOT_IMPL()};              // Read a symbolic link TODO: set the return value properly
        virtual std::vector<std::string> getdents(std::string path){NOT_IMPL()};
        // TODO: Implement opendir? Find out what its used for first
        // TODO: Maybe do getdir? its apparently deprecated
        // TODO: mknod, I have no reason for this (yet)
        virtual int mkdir(std::string path, int mode){NOT_IMPL()};
        virtual int unlink(std::string path){NOT_IMPL()};                         // Remove a node
        virtual int rmdir(std::string path){NOT_IMPL()};                          // Remove a (empty) directory
        virtual int symlink(std::string target, std::string linkpath){NOT_IMPL()};// Make a symbolic link
        virtual int rename(std::string oldpath, std::string newpath){NOT_IMPL()};
        virtual int link(std::string oldpath, std::string newpath){NOT_IMPL()};// Make a hardlink
        virtual int chmod(std::string path, int mode){NOT_IMPL()};
        virtual int chown(std::string path, int uid, int gid) { NOT_IMPL(); };
        virtual int truncate(std::string path, int size){NOT_IMPL()};// Change the size of a file
        virtual int utime(std::string path, void *ubuf){NOT_IMPL()}; // Change the timestamps of a file // TODO: Set the ubuf argument type
        virtual FileDescriptor *open(std::string path, int flags, int mode){NOT_IMPL()};
        virtual int close(FileDescriptor *fd){NOT_IMPL()};
        virtual std::string read(FileDescriptor *fd){NOT_IMPL()};// TODO: Maybe implement amount to read?
        virtual int write(std::string path, std::string data){NOT_IMPL()};
        virtual void statfs(std::string path){NOT_IMPL()};// Get filesystem stats // TODO: Set the return value properly
        // TODO: Maybe do flush? We don't really need this (maybe)
        // TODO: Maybe do fsync? Do we need?
        virtual std::string getxattr(std::string path, std::string name){NOT_IMPL()};
        virtual void listxattr(std::string path){NOT_IMPL()};  // TODO: Set the return value properly (either vector or map)
        virtual void removexattr(std::string path){NOT_IMPL()};// TODO: Set return value properly


        // TODO: THESE ARE ONLY TEMPORARY, REMOVE THEM ONCE I HAVE STUFF PROPERLY IMPLEMENTED
        virtual Inode *_find_inode(std::string path){NOT_IMPL()};

        virtual Inode *_find_inode_by_inode_num(int num){NOT_IMPL()};

        virtual DirectoryEntry *_find_directory_entry(std::string path){NOT_IMPL()};

        virtual bool exists(std::string path){NOT_IMPL()};

        virtual bool add_inode_to_path(std::string parent_path, std::string filename, Inode *inode){NOT_IMPL()};

    protected:
        std::string m_mount_point;
        Computer *m_computer;
        std::string m_fs_name = "???";
    };
}// namespace Blackhat