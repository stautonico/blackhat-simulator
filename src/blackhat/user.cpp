#include <blackhat/user.h>
#include <util/crypto.h>

Blackhat::User::User(int uid, std::string username, std::string password) {
  m_uid = uid;
  m_username = username;
  m_password = password;
}

void Blackhat::User::set_username(std::string username) {
  m_username = username;
}

void Blackhat::User::set_password(std::string password, bool is_plaintext) {
  if (is_plaintext)
    // MD5 hash the password
    m_password = md5(password);
  else
    m_password = password;
}

std::string Blackhat::User::get_password() { return m_password; }
