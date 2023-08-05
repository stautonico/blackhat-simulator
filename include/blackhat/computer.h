#pragma once

#include <blackhat/fs/filesystem.h>
#include <util/time.h>

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

  std::string temporary_read(std::string path);

private:
  Timestamp m_boottime;
  std::string m_hostname = "localhost"; // Fallback, will be overwritten by
                                        // something post-init

  std::map<std::string, Filesystem *> m_fs_mappings;
  // TODO: Add process'

  void _create_root_user();

  void _kinit();
  void _new_computer_kinit();
  void _create_fs_from_base(const std::filesystem::path &dir,
                            std::string basepath);
  void _post_fs_kinit();

  void _kernel_panic(std::string message);
};

} // namespace Blackhat