#pragma once

#include <map>
#include <string>
#include <vector>

// Forward declaration
//namespace Blackhat {
//    class Computer;
//}

#include <blackhat/computer.h>

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

    class Inode {
    public:
        friend class Ext4;

        std::string read();

        int write(std::string data);

        int append(std::string data);

        void increment_link_count() { m_link_count++; }

        void decrement_link_count() { m_link_count--; }

        int get_inode_number() { return m_inode_number; }
        std::string get_linked_name() {return m_points_to; }

        int get_mode();

        int get_uid() { return m_owner; }

        int get_gid() { return m_group_owner; }

        int get_link_count() { return m_link_count; }

        bool make_symlink(std::string point_to_path);

        enum Permission {
            READ,
            WRITE,
            EXECUTE
        };

        bool check_perm(Permission perm, Process *process);

        bool is_file() { return m_is_file; }
        bool is_directory() { return m_is_directory; }
        bool is_symlink() { return m_is_symlink; }


    private:
        Inode _clone();

        std::string m_name = "";
        std::string m_data = "";
        int m_inode_number = -1;

        int m_link_count = 0;

        int m_owner = 0;
        int m_group_owner = 0;

        int m_mode;


        std::string m_points_to = "";

        // TODO: Utilize these properly
        bool m_is_file = false;
        bool m_is_directory = false;
        bool m_is_symlink = false;
    };

    class DirectoryEntry {
    public:
        friend class Ext4;

        friend class Inode;

        DirectoryEntry(std::string name, Inode *inode);

        bool has_child(std::string name);

        bool add_child(std::string name, Inode *inode);

        DirectoryEntry *get_child(std::string name);

        bool remove_child(std::string name);

        Inode *get_inode() { return m_inode; }

        std::string get_name() {return m_name;}

        std::vector<std::string> get_children_names();


    private:
        Inode *m_inode;// TODO: Maybe replace this with inode number?
        // It would make the code slightly more complicated, but it would make
        // saving WAY easier.
        std::string m_name;

        // TODO: This? Idk about this. Maybe store it in a different data structure
        std::map<std::string, DirectoryEntry> m_dir_entries;// file name -> DirectoryEntry
    };

    class Ext4 {
    public:
        friend class Computer;

        Ext4();

        static Ext4 *make_standard_fs();

        int create(std::string path, int uid, int gid, int mode);

        int write(std::string path, std::string data);

        std::string read(std::string path);

        std::vector<std::string> readdir(std::string path);

        bool unlink(std::string path);

        bool rmdir(std::string path);

        bool exists(std::string path);

        bool rename(std::string oldpath, std::string newpath);

        // TODO: Shouldn't be public, write API later
        bool add_inode_to_path(std::string parent_path, std::string filename, Inode *inode);


    private:
        std::map<int, Inode *> m_inodes;// Inode number -> Inode *
        // TODO: Maybe store the actual inode here?

        Inode *m_root;
        DirectoryEntry m_root_directory_entry;

        Inode *_find_inode(std::string path);
        Inode *_find_inode_by_inode_num(int num);

        DirectoryEntry *_find_directory_entry(std::string path);

        int _create_inode(std::string path, int uid, int gid, int mode);


        int m_inode_accumulator = 3;// Start at something higher? We'll see
    };
}// namespace Blackhat
