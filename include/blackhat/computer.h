#pragma once

#include <blackhat/fs/filesystem.h>
#include <util/time.h>

#include <map>
#include <string>

namespace Blackhat {
class Computer {
public:
  Computer();

private:
  Timestamp m_boottime;
  std::string m_hostname = "localhost"; // Fallback, will be overwritten by
                                        // something post-init

  std::map<std::string, Filesystem *> m_fs_mappings;
  // TODO: Add process'

  void _create_root_user();

  void _kinit();
  void _new_computer_kinit();
  void _post_fs_kinit();

  void _kernel_panic(std::string message);
};
} // namespace Blackhat