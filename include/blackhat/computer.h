#pragma once

#include <string>
#include <vector>

#include <blackhat/fs/ext4.h>

// Forward declaration
namespace Blackhat {
    class Process;
}

#include <blackhat/process.h>

namespace Blackhat {
    class Computer {
    public:
        Computer();

        // TODO: Maybe not be public?
        void call_userland_init();

        int _exec(std::string path, std::vector<std::string> args);
        std::string _read(std::string path);

        std::vector<std::string> _readdir(std::string path);


    private:
        // TODO: boot time
        std::string m_hostname = "localhost";// Fallback, will be overwritten by
                                             // something post-init

        Ext4 *m_fs = nullptr;

        void _new_computer_kinit();

        void _kinit();
        void _post_fs_kinit();

        void _kernel_panic(std::string message);

        void _create_fs_from_base(const std::string &basepath, const std::string current_path);

    };
}// namespace Blackhat