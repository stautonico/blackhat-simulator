#include <algorithm>

#include <blackhat/fs/ext4.h>
#include <stdexcept>
#include <util/string.h>

namespace Blackhat {
    DirectoryEntry::DirectoryEntry(Blackhat::Inode *inode, std::string name) {
        m_inode = inode;
        m_name = name;
    }

    std::string Inode::read() {
        // TODO: Permission check
        return m_data;
    }

    int Inode::write(std::string data) {
        m_data = data;
        return m_data.size();
    }

    Inode Inode::_clone() {
        Inode newinode;
        newinode.m_name = m_name;
        newinode.m_data = m_data;
        newinode.m_inode_number = m_inode_number;
        newinode.m_link_count = m_link_count;
        newinode.m_mode = m_mode;
        return newinode;
    }

    Ext4::Ext4() : m_root_directory_entry(m_root, "/") {
        m_root = new Inode();
        m_root->m_name = "/";
        m_root->m_mode = 0755;
        m_root->m_inode_number = 2;
        m_inodes[2] = m_root;
        m_dir_entries[2] = std::vector<int>();
    }

    Ext4 *Ext4::make_standard_fs() {
        Ext4 *fs = new Ext4();

        // TODO: Add more here like /boot and /dev
        for (auto dir: {"/bin", "/etc", "/home", "/lib", "/root", "/run", "/sbin",
                        "/proc", "/tmp", "/usr", "/var"}) {
            if (dir == "/root")
                fs->create(dir, 0, 0, 0750);
            else if (dir == "/proc")
                fs->create(dir, 0, 0, 0555);
            else if (dir == "/tmp")
                fs->create(dir, 0, 0, 0777);
            else
                fs->create(dir, 0, 0, 0755);
        }

        return fs;
    }

    bool Ext4::create(std::string path, int uid, int gid, int mode) {
        // Do we really need this?
        // Can't we just put the src for `_create_inode` in here?
        return _create_inode(path, uid, gid, mode);
    }

    bool Ext4::_create_inode(std::string path, int uid, int gid, int mode) {
        // We have to find the parent first
        auto components = split(path, '/');
        auto parent_path = join(components, '/', 0, components.size() - 1);
        auto parent = _find_inode(parent_path);
        if (parent == nullptr)
            return false;// TODO: Find a way to return an error code (maybe return
                         //       int)

        // Create the new inode
        auto inode = new Inode();
        inode->m_name = components[components.size() - 1];
        inode->m_mode = mode;
        m_inodes[m_inode_accumulator] = inode;
        inode->m_inode_number = m_inode_accumulator;
        m_inode_accumulator++;
        // Add the inode to the parent's directory entries
        m_dir_entries[parent->m_inode_number].push_back(inode->m_inode_number);
        inode->m_link_count++;
        return true;
    }

    Inode *Ext4::_find_inode(std::string path) {
        auto components = split(path, '/');
        auto current = m_root->m_inode_number;
        for (const auto &component: components) {
            if (component.empty())
                continue;
            // Find all the children of the current inode
            auto children = m_dir_entries[current];
            // Find the child with the same name as the component
            auto child = std::find_if(
                    children.begin(), children.end(), [&component, this](int inode_number) {
                        return m_inodes[inode_number]->m_name == component;
                    });

            // If the child exists, set the current inode to the child
            if (child != children.end()) {
                current = *child;
            } else {
                return nullptr;
            }
        }
        return m_inodes[current];
    }

    int Ext4::write(std::string path, std::string data) {
        auto inode = _find_inode(path);
        if (inode == nullptr) {
            return -1;
        }
        inode->m_data = data;
        return data.size();
    }

    std::string Ext4::read(std::string path) {
        auto inode = _find_inode(path);
        if (inode == nullptr) {
            return std::string(1, '\0');
        }

        return inode->m_data;
    }
    std::vector<std::string> Ext4::readdir(std::string path) {
        auto inode = _find_inode(path);

        if (inode == nullptr) return {};

        auto entries = m_dir_entries[inode->m_inode_number];

        std::vector<std::string> names;

        for (auto entry: entries) {
            auto node = m_inodes[entry];
            if (node == nullptr) {
                throw std::runtime_error("Invalid inode number: " + entry);
            }

            names.push_back(node->m_name);
        }

        return names;
    }

    bool Ext4::exists(std::string path) {
        auto inode = _find_inode(path);
        return inode != nullptr;
    }

    bool Ext4::rmdir(std::string path) {
        auto components = split(path, '/');
        auto previous = -1;
        auto current = m_root->m_inode_number;


        for (const auto &component: components) {
            if (component.empty())
                continue;
            // Find all the children of the current inode
            auto children = m_dir_entries[current];
            // Find the child with the same name as the component
            auto child = std::find_if(
                    children.begin(), children.end(), [&component, this](int inode_number) {
                        return m_inodes[inode_number]->m_name == component;
                    });

            // If the child exists, set the current inode to the child
            if (child != children.end()) {
                previous = current;
                current = *child;
            } else {
                return false;
            }
        }

        // Only remove the directory IF ITS EMPTY
        if (m_dir_entries[current].size() > 0) {
            return false;
        }

        // current is the file to delete
        // previous is its parent
        auto entries = &m_dir_entries[previous];
        auto it = find(entries->begin(), entries->end(), current);
        if (it == entries->end()) return false;

        auto idx = it - entries->begin();

        // TODO: Don't remove the inode itself if the link count > 0
        // Erase the file from the directory entries
        entries->erase(entries->begin() + idx);

        // Erase the inode itself
        m_inodes.erase(current);

        return true;
    }

    bool Ext4::unlink(std::string path) {
        auto components = split(path, '/');
        auto previous = -1;
        auto current = m_root->m_inode_number;


        for (const auto &component: components) {
            if (component.empty())
                continue;
            // Find all the children of the current inode
            auto children = m_dir_entries[current];
            // Find the child with the same name as the component
            auto child = std::find_if(
                    children.begin(), children.end(), [&component, this](int inode_number) {
                        return m_inodes[inode_number]->m_name == component;
                    });

            // If the child exists, set the current inode to the child
            if (child != children.end()) {
                previous = current;
                current = *child;
            } else {
                return false;
            }
        }

        // current is the file to delete
        // previous is its parent
        auto entries = &m_dir_entries[previous];
        auto it = find(entries->begin(), entries->end(), current);
        if (it == entries->end()) return false;

        auto idx = it - entries->begin();

        // Erase the file from the directory entries
        entries->erase(entries->begin() + idx);

        auto inode = m_inodes[current];
        if (inode->m_link_count == 0) {
            // Erase the inode itself
            m_inodes.erase(current);
        }


        return true;
    }

    bool Ext4::rename(std::string oldpath, std::string newpath) {
        auto old_inode = _find_inode(oldpath);

        if (old_inode == nullptr) return false;

        // If the newpath exists, fail as well
        if (_find_inode(newpath) != nullptr) return false;

        // Make sure our new parent path exists
        auto split_path = split(newpath, '/');
        auto new_file_name = split_path.back();
        split_path.pop_back();
        auto new_parent_path = join(split_path, '/');

        auto new_parent_inode = _find_inode(new_parent_path);

        if (new_parent_inode == nullptr) return false;


        // Find the inode number of our old path parent
        split_path = split(oldpath, '/');
        split_path.pop_back();
        auto old_parent_path = join(split_path, '/');

        auto old_parent_inode = _find_inode(old_parent_path);


        // Remove the inode from its current parent
        auto entries = &m_dir_entries[old_parent_inode->m_inode_number];
        entries->erase(std::remove(entries->begin(), entries->end(), old_inode->m_inode_number), entries->end());

        // Add it to its new parent
        m_dir_entries[new_parent_inode->m_inode_number].push_back(old_inode->m_inode_number);
        // Change its name
        old_inode->m_name = new_file_name;
        return true;
    }


}// namespace Blackhat