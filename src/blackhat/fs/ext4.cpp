#include <blackhat/fs/ext4.h>
#include <util/string.h>

#include <algorithm>
#include <cstring>
#include <string>
#include <vector>

Blackhat::Ext4::Ext4() {
  m_root = new Inode();
  m_root->m_name = "/";
  m_root->m_mode = 0755;
  m_root->m_inode_number = 2;
  m_inodes[2] = m_root;
  m_directory_entries[2] = std::vector<int>();
}

Blackhat::Ext4 *Blackhat::Ext4::make_standard_fs() {
  Ext4 *fs = new Ext4();
  // TODO: Add more here like /boot and /dev
  for (auto dir : {"/bin", "/etc", "/home", "/lib", "/root", "/run", "/sbin",
                   "/proc", "/tmp", "/usr", "/var"}) {
    if (strcmp(dir, "/root") == 0)
      fs->create(dir, 0, 0, 0750);
    else if (strcmp(dir, "/proc") == 0)
      fs->create(dir, 0, 0, 0555);
    else if (strcmp(dir, "/tmp") == 0)
      fs->create(dir, 0, 0, 0777);
    else
      fs->create(dir, 0, 0, 0755);
  }

  return fs;
}

bool Blackhat::Ext4::_create_inode(std::string path, int uid, int gid,
                                   int mode) {
  // We have to find the parent first
  auto components = split(path, '/');
  auto parent_path = join(components, '/', 0, components.size() - 1);
  auto parent = _find_inode(parent_path);
  if (parent == nullptr)
    return false; // TODO: Find a way to return an error code (maybe return
                  //       int)

  // Create the new inode
  auto inode = new Inode();
  inode->m_name = components[components.size() - 1];
  inode->m_mode = mode;
  m_inodes[m_inode_accumulator] = inode;
  inode->m_inode_number = m_inode_accumulator;
  m_inode_accumulator++;
  // Add the inode to the parent's directory entries
  m_directory_entries[parent->m_inode_number].push_back(inode->m_inode_number);
  return true;
}

#include <iostream>

Blackhat::Inode *Blackhat::Ext4::_find_inode(std::string path) {
  auto components = split(path, '/');
  auto current = m_root->m_inode_number;
  for (const auto &component : components) {
    if (component.empty())
      continue;
    // Find all the children of the current inode
    auto children = m_directory_entries[current];
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

int Blackhat::Ext4::create(std::string path, int uid, int gid, int mode) {
  return _create_inode(path, uid, gid, mode);
}

int Blackhat::Ext4::write(std::string path, std::string data) {
  auto inode = _find_inode(path);
  if (inode == nullptr)
    return -1;
  inode->m_data = data;
  return data.size();
}

std::string Blackhat::Ext4::read(std::string path) {
  auto inode = _find_inode(path);
  if (inode == nullptr)
    return ""; // TODO: Find a way to return an error code and not an empty str

  // HACK: This is just a temporary hack to read a directory
  // Find if we're a directory

  return inode->m_data;
}

int Blackhat::Ext4::mv(std::string path, std::string new_path) { return 0; }
int Blackhat::Ext4::chmod(std::string path, int mode) { return 0; }
int Blackhat::Ext4::chown(std::string path, int uid, int gid) { return 0; }
int Blackhat::Ext4::rm(std::string path) { return 0; }

std::string Blackhat::Inode::get_name() { return m_name; }
int Blackhat::Inode::get_inode_number() { return m_inode_number; }

json Blackhat::Inode::serialize() {
  json j = {
      {"name", m_name},
      {"mode", m_mode},
      {"inode_number", m_inode_number},
      {"data", m_data},
  };

  return j;
}

json Blackhat::Ext4::serialize() {
  json j;

  j["inodes"] = json::object();

  // Serialize the inodes
  for (auto const &[ino_num, inode] : m_inodes) {
    j["inodes"][std::to_string(ino_num)] = inode->serialize();
  }

  // Serialize the directory entries
  j["directory_entries"] = json::object();
  for (auto const &[inode, entries] : m_directory_entries) {
    j["directory_entries"][std::to_string(inode)] = json::array();
    for (auto const &entry : entries) {
      j["directory_entries"][std::to_string(inode)].push_back(entry);
    }
  }

  j["root"] = m_root->serialize();

  return j;
}
