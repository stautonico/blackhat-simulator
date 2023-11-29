#pragma once

#include <string>
#include <vector>
#include <map>

// Forward declaration
//namespace Blackhat {
//    class Computer;
//}

#include <blackhat/computer.h>

namespace Blackhat {
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

        int get_mode() { return m_mode; }

        int get_uid() { return m_owner; }

        int get_gid() { return m_group_owner; }

        int get_link_count() { return m_link_count; }

        enum Permission {
            READ,
            WRITE,
            EXECUTE
        };

        bool check_perm(Permission perm, Process *process);


    private:
        Inode _clone();

        std::string m_name = "";
        std::string m_data = "";
        int m_inode_number = -1;

        int m_link_count = 0;

        int m_owner = 0;
        int m_group_owner = 0;

        int m_mode;
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

    private:
        Inode *m_inode; // TODO: Maybe replace this with inode number?
        // It would make the code slightly more complicated, but it would make
        // saving WAY easier.
        std::string m_name;

        // TODO: This? Idk about this. Maybe store it in a different data structure
        std::map<std::string, DirectoryEntry> m_dir_entries; // file name -> DirectoryEntry
    };

    class Ext4 {
    public:
        friend class Computer;

        Ext4();

        static Ext4 *make_standard_fs();

        bool create(std::string path, int uid, int gid, int mode);

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
        std::map<int, Inode *> m_inodes; // Inode number -> Inode *
        // TODO: Maybe store the actual inode here?

        Inode *m_root;
        DirectoryEntry m_root_directory_entry;

        Inode *_find_inode(std::string path);

        DirectoryEntry *_find_directory_entry(std::string path);

        bool _create_inode(std::string path, int uid, int gid, int mode);


        int m_inode_accumulator = 3; // Start at something higher? We'll see
    };
}
