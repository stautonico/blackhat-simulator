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
    class Inode {
    public:
        friend class Ext4;

        std::string read();
        int write(std::string data);

    private:
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