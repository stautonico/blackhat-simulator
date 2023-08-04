#include <blackhat/process.h>

#include <string>
#include <thread>
#include <utility>

Blackhat::Process::Process(std::string code) : m_interpreter(code, this) {
  m_state = ProcessState::TASK_STOPPED;
  m_exit_code = 0;
}

int Blackhat::Process::set_exit_code(int exit_code) {
  // This is just to make sure the exit code is in the range of 0-255
  // without using a `uint8_t` (which may or may not be supported by the
  // platform)
  if (exit_code > 255 || exit_code < 0)
    // AND the code with 0xFF to get the last 8 bits
    exit_code &= 0xFF; // 0xFF = 11111111 (255)

  m_exit_code = exit_code;

  return m_exit_code; // Return the "processed" exit code
}

void Blackhat::Process::_run(std::vector<std::string> args) {
  // This is the function that runs in the thread
  m_state = ProcessState::TASK_RUNNING;

  int exit_code = m_interpreter.run(args);

  set_exit_code(exit_code);

  // TODO: Set the exit code to 139 if main fails
  // TODO: Find a way to check if main failed (maybe exceptions?)

  m_state = ProcessState::EXIT_ZOMBIE;
};

void Blackhat::Process::start(std::vector<std::string> args) {
  std::thread t(&Blackhat::Process::_run, this, args);

  t.detach();
}

void Blackhat::Process::start_sync(std::vector<std::string> args) {
  _run(args);
}
std::string Blackhat::Process::get_env(std::string key) {
  // Try to find the key in the map
  auto it = m_environ.find(key);

  if (it == m_environ.end())
    return "";

  return it->second;
}
void Blackhat::Process::set_env(std::string key, std::string value) {
  // Try to find the key in the map
  auto it = m_environ.find(key);

  if (it == m_environ.end()) {
    // If the key is not found, insert it
    m_environ.insert(std::make_pair(key, value));
  } else {
    // If the key is found, update the value
    it->second = value;
  }
}
