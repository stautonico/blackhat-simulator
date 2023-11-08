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
    enum O {
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
        TRUNC = 00001000
    };

    class Inode {
    public:
        friend class Ext4;

        std::string read();
        int write(std::string data);

    private:
        Inode _clone();

        std::string m_name = "";
        std::string m_data = "";
        int m_inode_number = -1;

        int m_link_count = 0;

        int m_mode;
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

    private:
        std::map<int, Inode*> m_inodes; // Inode number -> Inode *
        std::map<int, std::vector<int>> m_dir_entries; // Inode num -> List of
                                                       // inode nums (children)

        Inode* m_root;

        Inode* _find_inode(std::string path);
        bool _create_inode(std::string path, int uid, int gid, int mode);

        int m_inode_accumulator = 3; // Start at something higher? We'll see
    };
}
