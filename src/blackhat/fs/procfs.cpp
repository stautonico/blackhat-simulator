
#include <blackhat/fs/procfs.h>

namespace Blackhat {
    ProcFS::ProcFS(std::string mount_point) {
        m_mount_point = mount_point;
    }

    std::vector<std::string> ProcFS::readdir(std::string path) {
        return {"/one", "/two", "/three"};
    }

}// namespace Blackhat