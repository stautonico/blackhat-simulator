#pragma once

#include <map>
#include <string>
#include <vector>

#include <blackhat/computer.h>
#include <blackhat/fs/basefs.h>

namespace Blackhat {
    class ProcFS : private BaseFS {
    public:
        ProcFS(std::string mount_point);

        std::vector<std::string> readdir(std::string path) override;


    private:
        std::string m_mount_point;

    };
}// namespace Blackhat
