#include <blackhat/process.h>


namespace Blackhat {
    Process::Process(std::string code, Computer *computer) : m_interpreter(code, this) {
        m_computer = computer;
    }

    void Process::start_sync(std::vector<std::string> args) {
        _run(args);
    }
    void Process::_run(std::vector<std::string> args) {
        // This is the function that runs in the thread
        //    m_state = ProcessState::TASK_RUNNING;

        int exit_code = m_interpreter.run(args);

        // set_exit_code(exit_code);

        // TODO: Set the exit code to 139 if main fails
        // TODO: Find a way to check if main failed (maybe exceptions?)

        //    m_state = ProcessState::EXIT_ZOMBIE;
    }

    std::string Process::getenv(std::string key) {
        // TODO: Maybe don't use exceptions?
        try {
            return m_environ.at(key);
        } catch (const std::out_of_range&) {
            return "";
        }
    }

    void Process::setenv(std::string key, std::string value) {
        m_environ[key] = value;
    }

    void Process::set_cwd(std::string path) {
        m_cwd = path;
    }
}