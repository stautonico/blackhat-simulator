#include <blackhat/computer.h>
#include <blackhat/interpreter.h>
#include <blackhat/process.h>

#include <iostream>
#include <sstream>

#define PID() t->m_process->m_pid

namespace Blackhat {
    Interpreter::Interpreter(std::string code, Process *process) {
        m_code = std::move(code);
        m_vm = new VM(false);
        m_process = process;
    }

    Interpreter::~Interpreter() {
        delete m_vm;
    }


    void Interpreter::_init_builtins() {
        m_vm->bind(
                m_vm->_main, "print(msg: str, newline:bool=True) -> None",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto msg_obj = CAST(Str &, args[0]);
                    auto msg = msg_obj.c_str();
                    auto newline = CAST(bool, args[1]);

                    t->_print(msg, newline);
                    return vm->None;
                },
                this);

        m_vm->bind(
                m_vm->_main, "input(prompt: str) -> str",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto prompt = CAST(Str &, args[0]);
                    const char *str = prompt.c_str();
                    return VAR(t->_input(str));
                },
                this);

        m_vm->bind(
                m_vm->_main, "require(module:str) -> None",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto module_obj = CAST(Str &, args[0]);
                    const char *module = module_obj.c_str();

                    t->_require(module);

                    return vm->None;
                },
                this);

        m_vm->bind(
                m_vm->_main, "_internal_get_env(key:str) -> str",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto key_obj = CAST(Str &, args[0]);
                    const char *key = key_obj.c_str();

                    auto result = t->m_process->getenv(key);
                    return VAR(result);
                },
                this);

        m_vm->bind(
                m_vm->_main, "_internal_set_env(key:str, value:str) -> None",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto key_obj = CAST(Str &, args[0]);
                    const char *key = key_obj.c_str();

                    auto value_obj = CAST(Str &, args[1]);
                    const char *value = value_obj.c_str();

                    t->m_process->setenv(key, value);
                    return vm->None;
                },
                this);

        m_vm->bind(
                m_vm->_main, "_syscall(call: int, *args)",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto syscall_id = CAST(int, args[0]);


                    // Extrapolate the *args
                    auto cmd_args = CAST(Tuple, args[1]);

                    switch (syscall_id) {
                        case SYSCALL_ID::SYS_READ: {
                            auto fd = CAST(int, cmd_args[0]);

                            auto result = t->m_process->m_computer->sys$read(fd, PID());

                            // Null value, aka doesn't exist, not empty string
                            if (result == std::string(1, '\0'))
                                return vm->None;

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_OPEN: {
                            auto path = CAST(Str &, cmd_args[0]).c_str();
                            auto flags = CAST(int, cmd_args[1]);
                            auto mode = CAST(int, cmd_args[2]);

                            // TODO: Make a macro for syscalls so we don't need to rewrite this each time
                            auto result = t->m_process->m_computer->sys$open(path, flags, mode, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_CLOSE: {
                            auto fd = CAST(int, cmd_args[0]);

                            auto result = t->m_process->m_computer->sys$close(fd, PID());
                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_WRITE: {
                            auto fd = CAST(int, cmd_args[0]);
                            auto data = CAST(Str &, cmd_args[1]).c_str();

                            return VAR(t->m_process->m_computer->sys$write(fd, data, PID()));
                        }

                        case SYSCALL_ID::SYS_GETCWD: {
                            auto result = t->m_process->m_computer->sys$getcwd(PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_CHDIR: {
                            // TODO: Maybe make this into a macro?
                            auto path = CAST(Str &, cmd_args[0]).c_str();

                            auto result = t->m_process->m_computer->sys$chdir(path, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_EXECVE: {
                            // TODO: Maybe make this into a macro?
                            auto path = CAST(Str &, cmd_args[0]).c_str();

                            auto argv_obj = CAST(List, cmd_args[1]);
                            auto envp_obj = CAST(Dict, cmd_args[2]);

                            // TODO: See if we can convert these automatically
                            std::vector<std::string> argv;

                            for (auto i = 0; i < argv_obj.size(); i++) {
                                argv.push_back(CAST(Str &, argv_obj[i]).c_str());
                            }

                            std::map<std::string, std::string> envp;

                            for (auto i = 0; i < envp_obj.keys().size(); i++) {
                                auto key = CAST(Str &, envp_obj.keys()[i]).c_str();
                                auto value = CAST(Str &, envp_obj.try_get(envp_obj.keys()[i])).c_str();
                                envp.insert({key, value});
                            }

                            auto result = t->m_process->m_computer->sys$execve(path, argv, envp, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_MKDIR: {
                            auto path = CAST(Str &, cmd_args[0]).c_str();

                            auto mode = CAST(int, cmd_args[1]);

                            auto result = t->m_process->m_computer->sys$mkdir(path, mode, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_RMDIR: {
                            auto path = CAST(Str &, cmd_args[0]).c_str();

                            auto result = t->m_process->m_computer->sys$rmdir(path, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_UNLINK: {
                            auto path = CAST(Str &, cmd_args[0]).c_str();

                            auto result = t->m_process->m_computer->sys$unlink(path, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_RENAME: {
                            auto oldpath = CAST(Str &, cmd_args[0]).c_str();
                            auto newpath = CAST(Str &, cmd_args[1]).c_str();

                            auto result = t->m_process->m_computer->sys$rename(oldpath, newpath, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_SETUID: {
                            auto uid = CAST(int, cmd_args[0]);
                            return VAR(t->m_process->m_computer->sys$setuid(uid, PID()));
                        }

                        case SYSCALL_ID::SYS_SETGID: {
                            auto gid = CAST(int, cmd_args[0]);
                            return VAR(t->m_process->m_computer->sys$setgid(gid, PID()));
                        }

                        case SYSCALL_ID::SYS_GETUID: {
                            return VAR(t->m_process->m_computer->sys$getuid(PID()));
                        }

                        case SYSCALL_ID::SYS_GETEUID: {
                            return VAR(t->m_process->m_computer->sys$geteuid(PID()));
                        }

                        case SYSCALL_ID::SYS_SETHOSTNAME: {
                            auto hostname = CAST(Str &, cmd_args[0]).c_str();

                            return VAR(t->m_process->m_computer->sys$sethostname(hostname, PID()));
                        }

                        case SYSCALL_ID::SYS_UNAME: {
                            auto result = t->m_process->m_computer->sys$uname(PID());

                            // Make an array and return it
                            List unameResult;
                            for (auto field: result) {
                                unameResult.push_back(VAR(field));
                            }

                            auto unameObject = VAR(std::move(unameResult));

                            return unameObject;
                        }

                        case SYSCALL_ID::SYS_LINK: {
                            auto oldpath = CAST(Str &, cmd_args[0]).c_str();
                            auto newpath = CAST(Str &, cmd_args[1]).c_str();

                            auto result = t->m_process->m_computer->sys$link(oldpath, newpath, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_SYMLINK: {
                            auto oldpath = CAST(Str &, cmd_args[0]).c_str();
                            auto newpath = CAST(Str &, cmd_args[1]).c_str();

                            auto result = t->m_process->m_computer->sys$symlink(oldpath, newpath, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_READLINK: {
                            auto pathname = CAST(Str &, cmd_args[0]).c_str();

                            auto result = t->m_process->m_computer->sys$readlink(pathname, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_STAT: {
                            auto pathname = CAST(Str &, cmd_args[0]).c_str();

                            auto result = t->m_process->m_computer->sys$stat(pathname, PID());

                            List statResult;
                            for (auto field: result) {
                                statResult.push_back(VAR(field));
                            }

                            auto statObject = VAR(std::move(statResult));

                            return statObject;
                        }

                        case SYSCALL_ID::SYS_GETDENTS: {
                            auto pathname = CAST(Str &, cmd_args[0]).c_str();

                            auto result = t->m_process->m_computer->sys$getdents(pathname, PID());

                            List ents;
                            for (auto r: result) {
                                ents.push_back(VAR(r));
                            }

                            return VAR(std::move(ents));
                        }

                        case SYSCALL_ID::SYS_CHOWN: {
                            auto pathname = CAST(Str &, cmd_args[0]).c_str();

                            auto owner = CAST(int, cmd_args[1]);
                            auto group = CAST(int, cmd_args[2]);

                            auto result = t->m_process->m_computer->sys$chown(pathname, owner, group, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_CHMOD: {
                            auto pathname = CAST(Str &, cmd_args[0]).c_str();
                            auto mode = CAST(int, cmd_args[1]);

                            auto result = t->m_process->m_computer->sys$chmod(pathname, mode, PID());

                            return VAR(result);
                        }

                        case SYSCALL_ID::SYS_KILL: {
                            printf("Our args are: [0]: %d, [1]: %d\n", cmd_args[0], cmd_args[1]);

                            auto pid = CAST(int, cmd_args[0]);
                            auto signal = CAST(int, cmd_args[1]);

                            auto result = t->m_process->m_computer->sys$kill(pid, signal, PID());

                            return VAR(result);
                        }

                        default:
                            throw std::runtime_error("Syscall " + std::to_string(syscall_id) + " not implemented!");
                            return vm->None;
                    }

                    return vm->None;
                },
                this);
    }

    void Interpreter::_print(std::string msg, bool newline) {
        if (newline) {
            std::cout << msg << std::endl;
        } else {
            std::cout << msg;
        }
    }

    int Interpreter::run(const std::vector<std::string> &args) {
        _init_builtins();

        m_vm->exec(m_code);

        auto python_args = _vector_to_python_string(args);

        auto return_code_obj = m_vm->eval("main(" + python_args + ")");

        // TODO: Support default return code if program doesn't return one
        auto return_code = py_cast<int>(m_vm, return_code_obj);

        return 0;
    }

    std::string Interpreter::_input(std::string prompt) {
        std::string input;
        std::cout << prompt;
        std::getline(std::cin, input);
        return input;
    }

    void Interpreter::_require(std::string module_name) {
        // Only import if we didn't already
        if (!(std::find(m_imported_modules.begin(), m_imported_modules.end(), module_name) !=
              m_imported_modules.end())) {
            auto result = m_process->m_computer->_read("/lib/" + module_name + ".so");

            m_vm->exec(result);

            m_imported_modules.push_back(module_name);

            // If we're importing errno, set it appropriately
            if (module_name == "errno")
                m_vm->exec("errno = " + std::to_string(m_process->get_errno()));
        }
    }

    std::string Interpreter::_vector_to_python_string(std::vector<std::string> in) {
        std::stringstream ss;

        // TODO: Support arguments that contain quotes (bunch them up)

        ss << "[";
        for (auto component: in) {
            // Replace all instances of " in the component with \"
            std::string output;

            for (auto c: component) {
                if (c == '"') {
                    output += "\\\"";
                } else {
                    output += c;
                }
            }

            ss << "\"" << output << "\",";
        }

        // Only remove the last comma IF we have a comma (aka not empty args)
        if (ss.str().back() != '[')
            ss.seekp(-1, std::ios_base::end);
        ss << "]";

        auto final = ss.str();
        return ss.str();
    }

    void Interpreter::set_errno(int errnum) {
        if (std::find(m_imported_modules.begin(), m_imported_modules.end(), "errno") != m_imported_modules.end()) {
            m_vm->exec("errno = " + std::to_string(errnum));
        }
    }
}// namespace Blackhat
