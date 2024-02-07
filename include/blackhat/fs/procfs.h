#pragma once

#include <map>
#include <string>
#include <vector>

#include <blackhat/computer.h>
#include <blackhat/fs/basefs.h>

namespace Blackhat {
    class ProcFS : private BaseFS {
    public:
        ProcFS(std::string mount_point, Computer *computer);

        std::vector<std::string> getdents(std::string path) override;

        std::string read(FileDescriptor *fd) override;

        FileDescriptor * open(std::string path, int flags, int mode) override;
        int close(Blackhat::FileDescriptor *fd) override;
    };
}// namespace Blackhat
