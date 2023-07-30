#include <blackhat/computer.h>
#include <blackhat/fs/ext4.h>
#include <blackhat/process.h>

#include <util/string.h>
#include <util/time.h>

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
  // TODO: Replace with exec /sbin/init
  this->m_fs_mappings["/"]->create("/sbin/init", 0, 0, 0755);
  this->m_fs_mappings["/"]->write("/sbin/init",
                                  "function main() {"
                                  "    while (true) {"
                                  "        var result = input('> ');"
                                  "        if (result == 'exit') {break;}"
                                  "        else {exec(result);}"
                                  "    }"
                                  "}");

  this->m_fs_mappings["/"]->create("/bin/test", 0, 0, 0755);
  this->m_fs_mappings["/"]->write("/bin/test", "function main() {"
                                               "    print('Hello, world!');"
                                               "}");

  call_init();

  //  Blackhat::Interpreter interpreter(
  //      this->m_fs_mappings["/"]->read("/sbin/init"));
  //  interpreter.run({});

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

void Blackhat::Computer::call_init() {
  auto file = this->m_fs_mappings["/"]->read("/sbin/init");

  // For now, just pretend it always exists
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