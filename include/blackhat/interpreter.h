#pragma once

// Forward declaration
namespace Blackhat {
    class Process;
}

//#include <pocketpy.h>
//using namespace pkpy; // idk about this, maybe change later

#include <string>
#include <vector>

#include <blackhat/vm.h>

namespace Blackhat {
    class Interpreter {
    public:
        friend class Process;
        Interpreter(std::string code, Blackhat::Process *process);
        ~Interpreter();

        int run(const std::vector<std::string> &args);
        void stop();

        void set_errno(int errnum);


    private:
        MyVM *m_vm = nullptr;

        Blackhat::Process *m_process = nullptr;

        std::string m_code;

        std::vector<std::string> m_imported_modules = {};

        void _init_builtins();

        void _print(std::string msg, bool newline = true);
        std::string _input(std::string prompt);
        int _exec(std::string path, std::vector<std::string> args);
        void _require(std::string module_name);


        std::string _vector_to_python_string(std::vector<std::string> in);

    };
}// namespace Blackhat