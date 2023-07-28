#pragma once

#include <string>

namespace Blackhat {
class User {
public:
  User(int uid, std::string username, std::string password);

  // Setters
  void set_username(std::string username);
  void set_password(std::string password, bool is_plaintext = true);

  // Getters
  std::string get_password();

private:
  int m_uid;
  std::string m_username;
  std::string m_password;

  // User info
  std::string m_fullname;
  std::string m_room_number;
  std::string m_work_phone;
  std::string m_home_phone;
  std::string m_other;

  std::string m_gecos; // The user's home directory
  std::string m_shell; // The user's shell
};
} // namespace Blackhat