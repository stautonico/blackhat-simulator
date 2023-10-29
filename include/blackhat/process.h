#pragma once

#include <blackhat/interpreter.h>

#include <string>
#include <vector>
#include <map>


namespace Blackhat {
    class Computer; // Forward declaration

    class Process {
    public:
        friend class Interpreter;
        Process(std::string code, Blackhat::Computer* computer);

        // TODO: Maybe not public?
        int set_exit_code(int exit_code);

        void start(std::vector<std::string> args);
        void start_sync(std::vector<std::string> args);

        std::string getenv(std::string key);
        void setenv(std::string key, std::string value);

        void set_cwd(std::string path);

    private:
        Blackhat::Computer* m_computer = nullptr;

        int m_pid;
        int m_ppid;

        std::string m_name;// Process name (argv[0]?)

        // TODO: Implement multithreadding support

        std::string m_cmdline;// <command> <args> (aka argv)

        std::string m_cwd;// Current working directory
        std::string m_exe;// Path to executable (isn't this supposed to be a link? or
                          // does procfs do that for us?)

        std::map<std::string, std::string> m_environ;// Environment variables

        Blackhat::Interpreter m_interpreter;

        void _run(std::vector<std::string> args);
    };
}// namespace Blackhat