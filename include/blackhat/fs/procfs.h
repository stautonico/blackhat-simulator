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


        // Operations that just fail since procfs shouldn't be modified
        int unlink(std::string path) override;
        int rename(std::string oldpath, std::string newpath) override;
        int rmdir(std::string path) override;
        // TECHNICALLY these shouldn't fail, but idc for now, maybe in the future I'll implement them properly
        int chown(std::string path, int uid, int gid) override;
        int chmod(std::string path, int mode) override;

    };
}// namespace Blackhat
