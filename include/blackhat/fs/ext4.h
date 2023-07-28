#pragma once

#include <blackhat/fs/filesystem.h>

#include <map>
#include <string>
#include <vector>

namespace Blackhat {
class Inode {
public:
  std::string get_name();

private:
  friend class Ext4;
  std::string m_name;
  std::string m_data;
  int m_inode_number;

  int m_mode;
};

class Ext4 : public Filesystem {
public:
  Ext4();

  static Ext4*make_standard_fs();

  int create(std::string path, int uid, int gid, int mode) override;
  int write(std::string path, std::string data) override;
  std::string read(std::string path) override;

  // TODO:
  int mv(std::string path, std::string new_path) override;
  int chmod(std::string path, int mode) override;
  int chown(std::string path, int uid, int gid) override;
  int rm(std::string path) override;

private:
  std::vector<Inode *> m_inodes;
  std::map<Inode *, std::vector<Inode *>> m_directory_entries;
  Inode *m_root;

  Inode *_find_inode(std::string path);
  bool _create_inode(std::string path, int uid, int gid, int mode);
};
} // namespace Blackhat