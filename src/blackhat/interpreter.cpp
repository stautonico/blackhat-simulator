#include <blackhat/computer.h>
#include <blackhat/interpreter.h>
#include <blackhat/process.h>

#include <iostream>

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
                m_vm->_main, "exec(path: str, args:list) -> int",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto path_obj = CAST(Str &, args[0]);
                    const char *path = path_obj.c_str();

                    auto args_obj = CAST(List &, args[1]);
                    std::vector<std::string> cmd_args;

                    for (auto i: args_obj) {
                        auto str_obj = CAST(Str &, i);
                        cmd_args.push_back(str_obj.c_str());
                    }

                    auto result = t->_exec(path, cmd_args);

                    return VAR(result);
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
                m_vm->_main, "_internal_read(path:str) -> str",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto path_obj = CAST(Str &, args[0]);
                    const char *path = path_obj.c_str();

                    auto result = t->_internal_read(path);
                    return VAR(result);
                },
                this);

        m_vm->bind(
                m_vm->_main, "_internal_readdir(path: str) -> list[str]",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());
                    auto path_obj = CAST(Str &, args[0]);
                    const char *path = path_obj.c_str();

                    auto result = t->_internal_readdir(path);

                    List l;

                    for (auto entry: result) {
                        l.push_back(VAR(entry));
                    }

                    return VAR(l);
                },
                this);

        m_vm->bind(
                m_vm->_main, "_internal_getcwd() -> str",
                [](VM *vm, ArgsView args) {
                    Interpreter *t = lambda_get_userdata<Interpreter *>(args.begin());

                    return VAR(t->_internal_getcwd());
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
                            auto path = CAST(Str &, cmd_args[0]).c_str();

                            auto result = t->m_process->m_computer->sys$read(path, t->m_process->m_pid);

                            // Null value, aka doesn't exist, not empty string
                            if (result == std::string(1, '\0'))
                                return vm->None;

                            return VAR(result);
                        }
                        case SYSCALL_ID::SYS_WRITE: {
                            auto path = CAST(Str &, cmd_args[0]).c_str();
                            auto data = CAST(Str &, cmd_args[1]).c_str();

                            return VAR(t->m_process->m_computer->sys$write(path, data, t->m_process->m_pid));
                        }
                        default:
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

    int Interpreter::_exec(std::string path, std::vector<std::string> args) {
        m_process->m_computer->_exec(path, args);
        return 0;
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

    std::string Interpreter::_internal_read(std::string path) {
        return m_process->m_computer->_read(path);
    }

    std::vector<std::string> Interpreter::_internal_readdir(std::string path) {
        return m_process->m_computer->_readdir(path);
    }

    std::string Interpreter::_internal_getcwd() {
        return m_process->m_cwd;
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