#pragma once

#include <blackhat/fs/filesystem.h>
#include <blackhat/fs/ext4.h>
#include <util/time.h>

#include <nlohmann/json.hpp>

using json = nlohmann::json;

#include <filesystem>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

namespace Blackhat {
class Computer {
public:
  Computer();

  void call_init();
  int temporary_exec(std::string path, std::vector<std::string> args);

  std::vector<Blackhat::Inode*> temporary_readdir(std::string path);

  std::string temporary_read(std::string path);

  json serialize();

private:
  Timestamp m_boottime;
  std::string m_hostname = "localhost"; // Fallback, will be overwritten by
                                        // something post-init

  std::map<std::string, Filesystem *> m_fs_mappings;
  // TODO: Add process'

  void _create_root_user();

  void _kinit();
  void _new_computer_kinit();
  void _create_fs_from_base(const std::string &basepath,
                            const std::string current_path);
  void _post_fs_kinit();

  void _kernel_panic(std::string message);
};

} // namespace Blackhat
