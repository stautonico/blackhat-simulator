#include <blackhat/process.h>
#include <util/string.h>

namespace Blackhat {
    Process::Process(std::string code, Computer *computer, int uid, int gid) : m_interpreter(code, this) {
        m_computer = computer;
        m_cwd = "/";

        m_ruid = uid;
        m_suid = uid;
        m_euid = uid;
        m_fsuid = uid;

        m_rgid = gid;
        m_sgid = gid;
        m_egid = gid;
        m_fsgid = gid;
    }

    void Process::start_sync(std::vector<std::string> args) {
        m_cmdline = join(args, ' ');
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
        } catch (const std::out_of_range &) {
            return "";
        }
    }

    void Process::setenv(std::string key, std::string value) {
        m_environ[key] = value;
    }

    void Process::set_cwd(std::string path) {
        m_cwd = path;
    }

    void Process::set_errno(int errnum) {
        m_errno = errnum;
        m_interpreter.set_errno(errnum);
    }

    void Process::add_file_descriptor(Blackhat::FileDescriptor* fd) {
        m_file_descriptors.insert({fd->get_fd(), fd});
        // Increment our fd accumulator
        _increment_fd_accumulator();
    }

    std::map<std::string, std::string> Process::get_entire_environment() {
        std::map<std::string, std::string> env_copy(m_environ); // Uses copy-construction
        return std::move(env_copy);
    }

    void Process::set_env_from_parent(std::map<std::string, std::string> env) {
        m_environ = std::move(env);
    }



    FileDescriptor *Process::get_file_descriptor(int fd) {
        auto it = m_file_descriptors.find(fd);

        if (it != m_file_descriptors.end()) return it->second;

        return nullptr;
    }

    void Process::delete_file_descriptor(int fd) {
        auto fd_obj = get_file_descriptor(fd);

        delete fd_obj;
    }

}// namespace Blackhat