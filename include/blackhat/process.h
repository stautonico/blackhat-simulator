#pragma once

#include <blackhat/interpreter.h>

#include <map>
#include <string>
#include <vector>

// Forward declaration
namespace Blackhat {
    class FileDescriptor;
}

#include <blackhat/fs/file_descriptor.h>


namespace Blackhat {
    class Computer;// Forward declaration

    class Process {
    public:
        friend class Interpreter;

        Process(std::string code, Blackhat::Computer *computer, int uid, int gid);

        // TODO: Maybe not public?
        int set_exit_code(int exit_code);

        void start(std::vector<std::string> args);

        void start_sync(std::vector<std::string> args);

        int get_pid() { return m_pid; }

        std::string getenv(std::string key);
        void setenv(std::string key, std::string value);

        void set_cwd(std::string path);
        std::string get_cwd() { return m_cwd; }

        void set_errno(int errnum);
        int get_errno() { return m_errno; }

        void set_pid(int pid) { m_pid = pid; }

        std::string get_cmdline() { return m_cmdline; }

        int get_fd_accumulator() { return m_fd_accumulator; }

        void set_uid(int uid) {m_suid = uid;}
        int get_uid() {return m_suid;}

        void set_gid(int gid) {m_sgid = gid;}
        int get_gid() {return m_sgid;}

        void set_euid(int uid) {m_euid = uid;}
        int get_euid() {return m_euid;}

        void set_egid(int gid) {m_egid = gid;}
        int get_egid() {return m_egid;}


        void set_fsuid(int uid) {m_fsuid = uid;}
        int get_fsuid() {return m_fsuid;}


        void set_fsgid(int gid) {m_fsgid = gid;}
        int get_fsgid() {return m_fsgid;}

        std::map<std::string, std::string> get_entire_environment();

        void set_env_from_parent(std::map<std::string, std::string> env);


        void add_file_descriptor(FileDescriptor* fd);
        FileDescriptor *get_file_descriptor(int fd);

    private:
        Blackhat::Computer *m_computer = nullptr;

        int m_pid;
        int m_ppid;

        std::string m_name;// Process name (argv[0]?)

        // TODO: Implement multithreadding support

        std::string m_cmdline = ""; // <command> <args> (aka argv)

        std::string m_cwd = "/"; // Current working directory
        std::string m_exe; // Path to executable (isn't this supposed to be a link? or
        // does procfs do that for us?)

        int m_errno = 0;

        // Possible exploit? We'll see
        int m_ruid = 0; // The original user's id
        int m_suid = 0; // A temporary one when we gain privileges
        int m_euid = 0; // Used for most checks
        int m_fsuid = 0; // Used for filesystem checks

        int m_rgid = 0;
        int m_sgid = 0;
        int m_egid = 0;
        int m_fsgid = 0;


        std::map<std::string, std::string> m_environ;// Environment variables

        Blackhat::Interpreter m_interpreter;

        int m_fd_accumulator = 3;                        // 0, 1, 2 reserved for stdin, stdout, and stderr
        std::map<int, FileDescriptor*> m_file_descriptors;// FD# -> FileDescriptor

        void _run(std::vector<std::string> args);

        void _increment_fd_accumulator() { m_fd_accumulator++; }
        void _decrement_fd_accumulator() { m_fd_accumulator--; }
    };
}// namespace Blackhat