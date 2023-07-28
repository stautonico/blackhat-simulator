#include <blackhat/computer.h>
#include <blackhat/fs/ext4.h>
#include <blackhat/interpreter.h>

#include <fstream>
#include <iostream>
#include <util/time.h>

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
  // TODO: Replace with exec /sbin/init
  this->m_fs_mappings["/"]->create("/sbin/init", 0, 0, 0755);
  this->m_fs_mappings["/"]->write(
      "/sbin/init", "function main() {"
                    "    while (true) {"
                    "        var result = input('> ');"
                    "        if (result == 'exit') {break;}"
                    "        else {print('You entered: ' + result);}"
                    "    }"
                    "}");

  Blackhat::Interpreter interpreter(
      this->m_fs_mappings["/"]->read("/sbin/init"));
  interpreter.run({});

  // this->sys$execve("/sbin/init");

  // We should never reach this point, but if we did, init exited
  // so, we should panic and TODO: reboot?
  this->_kernel_panic("Init exited");
}

void Blackhat::Computer::_new_computer_kinit() {
  // The steps to take when the computer is new (no filesystem)
  // TODO: Implement
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