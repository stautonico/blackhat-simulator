#include <algorithm>
#include <cstdint>

#include <blackhat/fs/ext4.h>
#include <stdexcept>
#include <util/string.h>

namespace Blackhat{
    DirectoryEntry::DirectoryEntry(std::string name, Blackhat::Inode *inode) {
        m_name = name;
        m_inode = inode;
    }

    bool DirectoryEntry::has_child(std::string name) {
        return m_dir_entries.find(name) != m_dir_entries.end();
    }

    DirectoryEntry *DirectoryEntry::get_child(std::string name) {
        if (has_child(name)) return &m_dir_entries.at(name);
        return nullptr;
    }

    bool DirectoryEntry::add_child(std::string name, Blackhat::Inode *inode) {
        if (has_child(name)) return false;

        DirectoryEntry newdirent(name, inode);

        m_dir_entries.insert({name, newdirent});
        return true;
    }

    bool DirectoryEntry::remove_child(std::string name) {
        if (!has_child(name)) return false;
        m_dir_entries.erase(name);
        return true;
    }

    std::string Inode::read() {
        // TODO: Permission check
        return m_data;
    }

    int Inode::write(std::string data) {
        m_data = data;
        return m_data.size();
    }

    int Inode::append(std::string data) {
        m_data += data;
        return data.size();
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

    bool Inode::check_perm(Inode::Permission perm, Process *process) {
        // If we're root, just return yes. Root can do whatever they want
        // EXCEPT for if we're executing. Even root can't execute a file without +x being set
        if (perm != Permission::EXECUTE) {
            if (process->get_fsuid() == 0 || process->get_fsgid() == 0) return true;
        }

        // Check the appropriate file permission bit based on the requested permission
        unsigned int permissionBit;
        switch (perm) {
            case Permission::READ:
                permissionBit = 0004;
                break;
            case Permission::WRITE:
                permissionBit = 0002;
                break;
            case Permission::EXECUTE:
                permissionBit = 0001;
                break;
            default:
                return false;
        }

        // Check if the public permission bit is set
        if (m_mode & permissionBit) return true;

        // Check if the group permission bit is set and the current user belongs to the group owner
        if (m_mode & permissionBit << 3 && m_group_owner == process->get_fsgid()) return true;

        // Check if the user permission bit is set and the current user is the owner
        if (m_mode & permissionBit << 6 && m_owner == process->get_fsuid()) return true;

        return false;
    }

    bool Inode::make_symlink(std::string point_to_path) {
        m_is_symlink = true;
        m_points_to = point_to_path;
        return true;
    }

    int Inode::get_mode() {
        uint16_t mode = m_mode;

        if (m_is_symlink) {
            mode = mode | S::IFLNK;
        }

        return mode;

    }


    Ext4::Ext4() : m_root_directory_entry("/", m_root) {
        m_root = new Inode();
        m_root->m_name = "/";
        m_root->m_mode = 0755 | S::IFDIR;
        m_root->m_inode_number = 2;
        m_inodes[2] = m_root;

        // We have to set our directory entries root again because it didn't exist at the top of this func
        m_root_directory_entry.m_inode = m_root;
        m_root_directory_entry.m_name = "/";
    }

    Ext4 *Ext4::make_standard_fs() {
        Ext4 *fs = new Ext4();

        // TODO: Add more here like /boot and /dev
        for (auto dir: {"/bin", "/etc", "/home", "/lib", "/root", "/run", "/sbin",
                        "/proc", "/tmp", "/usr", "/var"}) {
            if (dir == "/root")
                fs->create(dir, 0, 0, 0750 | S::IFDIR);
            else if (dir == "/proc")
                fs->create(dir, 0, 0, 0555 | S::IFDIR);
            else if (dir == "/tmp")
                fs->create(dir, 0, 0, 0777 | S::IFDIR);
            else
                fs->create(dir, 0, 0, 0755 | S::IFDIR);
        }

        return fs;
    }

    int Ext4::create(std::string path, int uid, int gid, int mode) {
        // Do we really need this?
        // Can't we just put the src for `_create_inode` in here?
        return _create_inode(path, uid, gid, mode);
    }

    bool Ext4::add_inode_to_path(std::string parent_path, std::string filename, Blackhat::Inode *inode) {
        // We have to follow the path components and find each directory entry
        auto components = split(parent_path, '/');

        std::vector<DirectoryEntry *> current;
        current.push_back(&m_root_directory_entry);

        for (const auto &component: components) {
            if (component.empty()) continue;// TODO: ?
            if (!current.back()->has_child(component)) return false;

            current.push_back(current.back()->get_child(component));
        }


        // If we made it here, current should be our final directory
        current.back()->add_child(filename, inode);
        return true;
    }

    int Ext4::_create_inode(std::string path, int uid, int gid, int mode) {
        // We have to find the parent first
        auto components = split(path, '/');
        auto parent_path = join(components, '/', 0, components.size() - 1);

        // Make sure the parent exists
        auto parent_dirent = _find_directory_entry(parent_path);

        if (parent_dirent == nullptr) return false;

        // Create the new inode
        auto inode = new Inode();
        inode->m_mode = mode;
        m_inodes[m_inode_accumulator] = inode;
        inode->m_inode_number = m_inode_accumulator;
        m_inode_accumulator++;
        // Add the inode to the parent's directory entries
        auto result = add_inode_to_path(parent_path, components[components.size() - 1], inode);
        // This should never fail, but it doesn't hurt to check
        if (!result) {
            // Delete the inode we just created
            m_inodes.erase(inode->m_inode_number);
            delete inode;
            return -1;
        }

        // Figure out what we tried to make based on the mode
        if (ISDIR(inode->m_mode)) {
            inode->m_is_directory = true;
        } else if (ISLNK(inode->m_mode)) {
            inode->m_is_symlink = true;
        } else if (ISREG(inode->m_mode)) {
            inode->m_is_file = true;
        }


        inode->m_link_count++;
        return inode->m_inode_number;
    }

    Inode *Ext4::_find_inode(std::string path) {
        auto result = _find_directory_entry(path);

        if (result == nullptr) return nullptr;
        return result->m_inode;
    }

    Inode *Ext4::_find_inode_by_inode_num(int num) {
        if (m_inodes.find(num) != m_inodes.end()) {
            return m_inodes[num];
        }
        return nullptr;
    }

    DirectoryEntry *Ext4::_find_directory_entry(std::string path) {
        auto components = split(path, '/');
        // TODO: I hate this, but its the only way I can think of how to fix this (3:27 am)
        std::vector<DirectoryEntry *> current;
        current.push_back(&m_root_directory_entry);


        for (const auto &component: components) {
            if (component.empty())
                continue;// TODO: Don't continue?

            current.push_back(current.back()->get_child(component));
            if (current.back() == nullptr) return nullptr;
        }

        return current.back();
    }

    std::vector<std::string> DirectoryEntry::get_children_names() {
        std::vector<std::string> names;

        for (auto it = m_dir_entries.begin(); it != m_dir_entries.end(); ++it) {
            names.push_back(it->first);
        }

        return names;
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

        // If we have a symlink, read from the linked node
        if (inode->is_symlink()) {
            auto linked_node = _find_inode(inode->m_points_to);
            if (linked_node == nullptr) {
                return std::string(1, '\0'); // Technically broken links don't resolve to anything
            } else {
                return linked_node->m_data;
            }
        }

        return inode->m_data;
    }

    std::vector<std::string> Ext4::readdir(std::string path) {
        auto dir_entry = _find_directory_entry(path);

        if (dir_entry == nullptr) return {};

        auto entries = dir_entry->m_dir_entries;

        std::vector<std::string> names;

        for (auto e: entries) names.push_back(e.first);

        return names;
    }

    bool Ext4::exists(std::string path) {
        auto inode = _find_inode(path);
        return inode != nullptr;
    }

    bool Ext4::rmdir(std::string path) {
        // Step 1: Find the parent directory entry
        auto components = split(path, '/');
        auto previous = -1;

        auto file_to_delete = components.back();
        components.pop_back();

        auto parent_dir_entry = _find_directory_entry(join(components, '/'));
        if (parent_dir_entry == nullptr) return false;

        // Step 2: Get the inode for later
        auto to_delete_direntry = parent_dir_entry->get_child(file_to_delete);

        if (to_delete_direntry == nullptr) return false;

        auto inode = to_delete_direntry->m_inode;

        // Step 3: Remove the directory entry from the parent
        // Check if the directory is empty before removing it
        if (to_delete_direntry->m_dir_entries.size() != 0) return false;

        // TODO: Only remove the entry if it is a directory (currently removes any dir entry regardless of type)

        auto remove_result = parent_dir_entry->remove_child(file_to_delete);

        if (!remove_result) return false;

        // Reduce the link count
        inode->m_link_count--;

        if (inode->m_link_count == 0) {
            m_inodes.erase(inode->m_inode_number);
            // Delete the inode (since we have no links to it)
            delete inode;
        }

        return true;
    }

    bool Ext4::unlink(std::string path) {
        // TODO: Don't unlink until all fds to the entry is gone
        // Step 1: Find the parent directory entry
        auto components = split(path, '/');
        auto previous = -1;

        auto file_to_delete = components.back();
        components.pop_back();

        auto parent_dir_entry = _find_directory_entry(join(components, '/'));
        if (parent_dir_entry == nullptr) return false;

        // Step 2: Get the inode for later
        auto to_delete_direntry = parent_dir_entry->get_child(file_to_delete);

        if (to_delete_direntry == nullptr) return false;

        auto inode = to_delete_direntry->m_inode;

        // Step 3: Remove the directory entry from the parent
        auto remove_result = parent_dir_entry->remove_child(file_to_delete);

        if (!remove_result) return false;

        // Reduce the link count
        inode->m_link_count--;

        if (inode->m_link_count == 0) {
            m_inodes.erase(inode->m_inode_number);
            // Delete the inode (since we have no links to it)
            delete inode;
        }

        return true;
    }

    bool Ext4::rename(std::string oldpath, std::string newpath) {
        auto old_dirent = _find_directory_entry(oldpath);

        if (old_dirent == nullptr) return false;

        auto new_dirent = _find_directory_entry(newpath);
        if (new_dirent != nullptr) return false;

        // Create a new dirent in the new path pointing to the inode
        // Find the parent (new path)
        auto split_path = split(newpath, '/');
        auto new_file_name = split_path.back();
        split_path.pop_back();
        auto parent_path = join(split_path, '/');

        auto parent_dirent = _find_directory_entry(parent_path);

        if (parent_dirent == nullptr) return false;

        auto add_result = parent_dirent->add_child(new_file_name, old_dirent->m_inode);

        if (!add_result) return false;

        // Now that we added the new dirent, remove the old one
        // Find the old parent
        auto old_split_path = split(oldpath, '/');
        auto old_file_name = old_split_path.back();
        old_split_path.pop_back();
        auto old_parent_path = join(old_split_path, '/');

        auto old_parent_dirent = _find_directory_entry(old_parent_path);

        // Should never happen but doesn't hurt to check
        if (old_parent_dirent == nullptr) return false;

        auto remove_result = old_parent_dirent->remove_child(old_file_name);

        return remove_result;
    }


}// namespace Blackhat