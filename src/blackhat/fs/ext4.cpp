#include <algorithm>

#include <blackhat/fs/ext4.h>
#include <stdexcept>
#include <util/string.h>

namespace Blackhat {
    std::string Inode::read() {
        // TODO: Permission check
        return m_data;
    }

    int Inode::write(std::string data) {
        m_data = data;
        return m_data.size();
    }

    Ext4::Ext4() {
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

    int Ext4::create(std::string path, int uid, int gid, int mode) {
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


}// namespace Blackhat