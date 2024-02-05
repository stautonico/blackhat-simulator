#pragma once

#include <map>
#include <string>
#include <vector>

#include <blackhat/computer.h>
#include <blackhat/fs/basefs.h>
#include <blackhat/fs/file_descriptor.h>


namespace Blackhat {
    class Inode {
    public:
        friend class Ext4;

        std::string read();

        int write(std::string data);

        int append(std::string data);

        void increment_link_count() { m_link_count++; }

        void decrement_link_count() { m_link_count--; }

        int get_inode_number() { return m_inode_number; }
        std::string get_linked_name() { return m_points_to; }

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

        std::string get_name() { return m_name; }

        std::vector<std::string> get_children_names();


    private:
        Inode *m_inode;// TODO: Maybe replace this with inode number?
        // It would make the code slightly more complicated, but it would make
        // saving WAY easier.
        std::string m_name;

        // TODO: This? Idk about this. Maybe store it in a different data structure
        std::map<std::string, DirectoryEntry> m_dir_entries;// file name -> DirectoryEntry
    };

    class Ext4 : private BaseFS {
    public:
        friend class Computer;

        Ext4();

        static Ext4 *make_standard_fs();

        FileDescriptor *open(std::string path, int flags, int mode) override;
        int unlink(std::string path) override;


        int create(std::string path, int uid, int gid, int mode);

        int write(std::string path, std::string data);

        std::string read(std::string path);

        std::vector<std::string> readdir(std::string path);

//        bool unlink(std::string path);

//        bool rmdir(std::string path);

        bool exists(std::string path);

//        bool rename(std::string oldpath, std::string newpath);

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
