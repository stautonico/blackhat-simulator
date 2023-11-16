#include <blackhat/user.h>
#include <sstream>

namespace Blackhat {
    User::User(int uid, std::string username) {
        m_uid = uid;
        m_gid = uid;// TODO: Maybe have a different constructor for uid+gid?
        m_username = username;
        // TODO: Maybe change: Automatically assume that the home dir is /home/<username>
        m_dir = "/home/" + m_username;
        // TODO: Maybe change: Automatically assume that the shell is /bin/sh
        m_shell = "/bin/sh";

    }

    std::string User::passwd_entry() const {
        std::stringstream ss;

        ss << m_username << ":";
        ss << m_password << ":";// TODO: Maybe don't do this and do /etc/shadow instead?
        ss << m_uid << ":";
        ss << m_gid << ":";
        ss << m_full_name << "," << m_room_num << "," << m_work_phone << "," << m_home_phone << "," << m_other << ":";// GECOS
        ss << m_dir << ":";
        ss << m_shell;

        return ss.str();
    }
    void User::set_password(std::string password, bool is_plaintext) {
        if (is_plaintext) {
            // TODO: Hash the password
        }

        m_password = password;
    }
}// namespace Blackhat