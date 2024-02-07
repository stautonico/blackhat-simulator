#pragma once

#include <map>
#include <string>
#include <vector>
#include <stdexcept>

namespace Blackhat {
    class DirectoryEntry;
}


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
        BaseFS() {};

        ~BaseFS() {};

        inline std::string get_mount_point() {
            return m_mount_point;
        }

        // https://www.cs.hmc.edu/~geoff/classes/hmc.cs135.201001/homework/fuse/fuse_doc.html
        virtual int getattr(std::string path) {
            throw std::runtime_error("getattr() is not implemented!");
        }; // the 'stat' command basically // TODO: set the return value properly
        virtual void readlink() {
            throw std::runtime_error("readlink() is not implemented!");
        }; // Read a symbolic link TODO: set the return value properly
        virtual std::vector<std::string> readdir(std::string path) {
            throw std::runtime_error("readdir() is not implemented!");
        };

        // TODO: Implement opendir? Find out what its used for first
        // TODO: Maybe do getdir? its apparently deprecated
        // TODO: mknod, I have no reason for this (yet)
        virtual int mkdir(std::string path, int mode) { throw std::runtime_error("mkdir() is not implemented!"); };;

        virtual int unlink(std::string path) {
            throw std::runtime_error("unlink() is not implemented!");
        }; // Remove a node
        virtual int rmdir(std::string path) {
            throw std::runtime_error("rmdir() is not implemented!");
        }; // Remove a (empty) directory
        virtual int symlink(std::string target, std::string linkpath) {
            throw std::runtime_error("symlink() is not implemented!");
        }; // Make a symbolic link
        virtual int rename(std::string oldpath, std::string newpath) {
            throw std::runtime_error("rename() is not implemented!");
        };

        virtual int link(std::string oldpath, std::string newpath) {
            throw std::runtime_error("link() is not implemented!");
        }; // Make a hardlink
        virtual int chmod(std::string path, int mode) { throw std::runtime_error("chmod() is not implemented!"); };

        virtual int chown(std::string path, int uid, int gid) {
            throw std::runtime_error("chown() is not implemented!");
        };

        virtual int truncate(std::string path, int size) {
            throw std::runtime_error("truncate() is not implemented!");
        }; // Change the size of a file
        virtual int utime(std::string path, void *ubuf) {
            throw std::runtime_error("utime() is not implemented!");
        }; // Change the timestamps of a file // TODO: Set the ubuf argument type
        virtual FileDescriptor *open(std::string path, int flags, int mode) {
            throw std::runtime_error("open() is not implemented!");
        };

        virtual std::string read(std::string path) {
            throw std::runtime_error("read() is not implemented!");
        }; // TODO: Maybe implement offset?
        virtual int write(std::string path, std::string data) {
            throw std::runtime_error("write() is not implemented!");
        };

        virtual void statfs(std::string path) {
            throw std::runtime_error("statfs() is not implemented!");
        }; // Get filesystem stats // TODO: Set the return value properly
        // TODO: Maybe do flush? We don't really need this (maybe)
        // TODO: Maybe do fsync? Do we need?
        virtual std::string getxattr(std::string path, std::string name) {
            throw std::runtime_error("getxattr() is not implemented!");
        };

        virtual void listxattr(std::string path) {
            throw std::runtime_error("listxattr() is not implemented!");
        }; // TODO: Set the return value properly (either vector or map)
        virtual void removexattr(std::string path) {
            throw std::runtime_error("removexattr() is not implemented!");
        }; // TODO: Set return value properly


        // TODO: THESE ARE ONLY TEMPORARY, REMOVE THEM ONCE I HAVE STUFF PROPERLY IMPLEMENTED
        virtual Inode *_find_inode(std::string path) { throw std::runtime_error("Not implemented!"); };

        virtual Inode *_find_inode_by_inode_num(int num) { throw std::runtime_error("Not implemented!"); };

        virtual DirectoryEntry *_find_directory_entry(std::string path) {
            throw std::runtime_error("Not implemented!");
        };

        virtual bool exists(std::string path) { throw std::runtime_error("Not implemented!"); };

        virtual bool add_inode_to_path(std::string parent_path, std::string filename, Inode *inode) {
            throw std::runtime_error("Not implemented!");
        };

    protected:
        inline std::string _strip_mount_point(std::string path) {
            if (m_mount_point == path.substr(0, m_mount_point.length()))
                path.erase(0, m_mount_point.length());

            // Make sure we still have a '/' at the beginning
            if (path.substr(0, 1) != "/")
                path = "/" + path;

            return path;
        }

    private:
        std::string m_mount_point;

    };
}