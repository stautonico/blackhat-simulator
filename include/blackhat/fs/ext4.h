#pragma once

#include <blackhat/fs/filesystem.h>

#include <nlohmann/json.hpp>
using json = nlohmann::json;

#include <map>
#include <string>
#include <vector>

namespace Blackhat {
class Inode {
public:
  std::string get_name();
  int get_inode_number();

private:
  friend class Ext4;
  std::string m_name;
  std::string m_data;
  int m_inode_number;

  int m_mode;

  json serialize();
};

class Ext4 : public Filesystem {
public:
  Ext4();

  static Ext4 *make_standard_fs();

  int create(std::string path, int uid, int gid, int mode) override;
  int write(std::string path, std::string data) override;
  std::string read(std::string path) override;

  std::vector<std::string> readdir(std::string path) override;

  // TODO:
  int mv(std::string path, std::string new_path) override;
  int chmod(std::string path, int mode) override;
  int chown(std::string path, int uid, int gid) override;
  int rm(std::string path) override;

  json serialize() override;

private:

  std::map<int, Inode *> m_inodes; // Inode number -> Inode *
  std::map<int, std::vector<int>> m_directory_entries; // Inode number -> Vector
                                                       // of inode numbers
                                                       // (children)
  Inode *m_root;

  Inode *_find_inode(std::string path);
  bool _create_inode(std::string path, int uid, int gid, int mode);

  int m_inode_accumulator = 3;
};
} // namespace Blackhat