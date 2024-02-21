#include <atomic>
#include <iostream>
#include <signal.h>
#include <thread>

#define PK_USER_CONFIG_H
#include <pocketpy.h>
using namespace pkpy;// idk about this, maybe change later

class MyVM : public VM {
public:
    // use atomic to protect the flag
    bool _flag = false;

    MyVM(bool enable_os) : VM(enable_os) {
        this->_ceval_on_step = [](VM *_vm, Frame *frame, Bytecode bc) {
            MyVM *vm = (MyVM *) _vm;
            std::cout << "Step..." << std::endl;
            if (vm->_flag) {
                std::cout << "OUR FLAG IS SET! SIGNALING KB INTERRUPT!" << std::endl;
                vm->_flag = false;
                vm->KeyboardInterrupt();
            }
        };
    }
    void KeyboardInterrupt() {
        std::cout << "Our interrupt is running!" << std::endl;
        _error(py_var(this, "KeyboardInterrupt"));
        std::cout << "Error sent!" << std::endl;
    }
};