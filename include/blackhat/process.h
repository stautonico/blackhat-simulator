#pragma once

// Forward declaration
//namespace Blackhat{class Interpreter;}
//namespace Blackhat{class Process;}
#include <blackhat/interpreter.h>

#include <map>
#include <string>
#include <vector>

namespace Blackhat {

enum class ProcessState {
  TASK_RUNNING,
  TASK_INTERRUPTIBLE,
  TASK_UNINTERRUPTIBLE,
  TASK_STOPPED,
  TASK_TRACED,
  EXIT_DEAD,
  EXIT_ZOMBIE,
  TASK_DEAD,
  TASK_WAKEKILL,
  TASK_WAKING,
  TASK_PARKED,
  TASK_NOLOAD,
  TASK_NEW,
  TASK_STATE_MAX
};

class Process {
public:
  explicit Process(std::string code);

  // TODO: Maybe not public?
  int set_exit_code(int exit_code);

  void start(std::vector<std::string> args);
  void start_sync(std::vector<std::string> args);

  std::string get_env(std::string key);
  void set_env(std::string key, std::string value);

private:
  int m_pid;
  int m_ppid;
  ProcessState m_state;
  int m_exit_code;
  // TODO: Store children
  // NOTE: I think its reasonable to use pointers to point to children
  //       and maybe even parent process since the processes dont get
  //       saved when the game is saved, so no need to worry about
  //       dangling pointers

  int m_uid;   // User identifier
  int m_euid;  // effective UID used for privilege checks
  int m_suid;  // saved UID used to support switching permissions
  int m_fsuid; // UID used for filesystem access checks (used by NFS for
               // example)

  int m_gid;   // Group identifier
  int m_egid;  // effective GID used for privilege checks
  int m_sgid;  // saved GID used to support switching permissions
  int m_fsgid; // GID used for filesystem access checks (used by NFS for
               // example)

  std::string m_name; // Process name (argv[0]?)

  // TODO: Implement multithreadding support

  std::string m_cmdline; // <command> <args> (aka argv)

  std::string m_cwd; // Current working directory
  std::string m_exe; // Path to executable (isn't this supposed to be a link? or
                     // does procfs do that for us?)

  std::map<std::string, std::string> m_environ; // Environment variables

  Interpreter m_interpreter;

  void _run(std::vector<std::string> args);
};
} // namespace Blackhat