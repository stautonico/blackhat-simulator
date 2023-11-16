#pragma once

#include <string>

namespace Blackhat {
    class User {
    public:
        User(int uid, std::string username);

        std::string passwd_entry() const;
        void set_password(std::string password, bool is_plaintext = true);

        void set_home_dir(std::string dir) { m_dir = dir; }

    private:
        // TODO: gid?
        std::string m_username = "";
        std::string m_password = "";// TODO: How to store hash?
        int m_uid = 0;
        int m_gid = 0;
        std::string m_dir = "";
        std::string m_shell = "";

        // GECOS fields
        std::string m_full_name = "";
        std::string m_room_num = "";
        std::string m_work_phone = "";
        std::string m_home_phone = "";
        std::string m_other = "";
    };
}// namespace Blackhat