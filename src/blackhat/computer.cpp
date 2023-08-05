#include <blackhat/computer.h>
#include <blackhat/fs/ext4.h>
#include <blackhat/process.h>

#include <util/string.h>
#include <util/time.h>

#include <filesystem>
#include <fstream>
#include <iostream>

Blackhat::Computer g_computer;

Blackhat::Computer::Computer() {
  this->m_boottime = Timestamp();
  this->_kinit();
}
void Blackhat::Computer::_kinit() {
  // The kernel's init function (not to be confused with userland init:
  // /sbin/init)
  bool has_filesystem = false;
  this->_create_root_user();

  // Check if `fs.bin` exists
  std::ifstream fs_bin("fs.bin");
  Blackhat::Ext4 *fs;

  if (fs_bin.good()) {
    has_filesystem = true;
    // TODO: Load the filesystem into `*fs`
  } else {
    fs = Blackhat::Ext4::make_standard_fs();
  }

  fs_bin.close();

  m_fs_mappings["/"] = fs;

  // If we didn't have a filesystem, we need to do some post-fs init
  if (!has_filesystem)
    this->_new_computer_kinit();

  this->_post_fs_kinit();

  // Spawn the root process (init) aka userland init
  call_init();

  // We should never reach this point, but if we did, init exited
  // so, we should panic and TODO: reboot?
  this->_kernel_panic("Init exited");
}

void Blackhat::Computer::_create_fs_from_base(const std::filesystem::path &dir,
                                              std::string basepath) {
  // Loop through each directory/file in the base directory and create it
  // in the game's filesystem
  for (const auto &entry : std::filesystem::directory_iterator(dir)) {
    if (entry.is_directory()) {
      _create_fs_from_base(entry.path(), basepath);
    } else {
      // This code is gross but it'll do for now
      // TODO: Set the correct metadata and ACLs
      this->m_fs_mappings["/"]->create(erase(entry.path().string(), basepath),
                                       0, 0, 0755);
      this->m_fs_mappings["/"]->write(
          erase(entry.path().string(), basepath),
          std::string(std::istreambuf_iterator<char>(
                          std::ifstream(entry.path().string(), std::ios::binary)
                              .rdbuf()),
                      std::istreambuf_iterator<char>()));
    }
  }
}

void Blackhat::Computer::_new_computer_kinit() {
  // The steps to take when the computer is new (no filesystem)
  // These setups usually relate to creating the base files in the fs
  // For now, this file simply follows the structure of the physical "base"
  // directory and copies it into the game, but maybe in the future,
  // this will change

  std::string path;

  if (std::filesystem::exists("base"))
    path = "base";
  else if (std::filesystem::exists("../base"))
    path = "../base";
  else
    _kernel_panic("No base directory found: Cannot initialize filesystem");

  _create_fs_from_base(path, path);
}

void Blackhat::Computer::_post_fs_kinit() {
  // The steps to take after the filesystem has been initialized
  // TODO: Implement
}

void Blackhat::Computer::_create_root_user() {
  // Create the root user
  // TODO: Implement
}

void Blackhat::Computer::_kernel_panic(std::string message) {
  std::cout << "Kernel panic - not syncing: " << message << std::endl;
  exit(1);
}

void Blackhat::Computer::call_init() {
  auto file = this->m_fs_mappings["/"]->read("/sbin/init");

  if (file.empty()) {
    // Kernel panic message should be:
    // "Kernel panic on boot: run-init: /sbin/init: No such file or directory."
    _kernel_panic("/sbin/init: No such file or directory");
  }

  Blackhat::Process process(file);
  process.start_sync({});
}

int Blackhat::Computer::temporary_exec(std::string path,
                                       std::vector<std::string> args) {
  // Try to find the file in the filesystem
  auto file = this->m_fs_mappings["/"]->read(path);

  // Open /tmp/log

  if (file.empty()) {
    std::cout << "Command not found: " << path << std::endl;
    return 1;
  } else {
    Blackhat::Process process(file);
    process.start_sync(args);
    return 0;
  }
}

std::string Blackhat::Computer::temporary_read(std::string path) {
  return this->m_fs_mappings["/"]->read(path);
}