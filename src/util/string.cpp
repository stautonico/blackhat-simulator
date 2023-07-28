#include <util/string.h>

#include <string>
#include <vector>

std::vector<std::string> split(std::string str, char delim) {
  std::vector<std::string> result;
  std::string current = "";
  for (char c : str) {
    if (c == delim) {
      result.push_back(current);
      current = "";
    } else {
      current += c;
    }
  }
  result.push_back(current);
  return result;
}

std::string join(std::vector<std::string> components, char delim, int start,
                 int end) {
  std::string result = "";
  for (int i = start; i < end; i++) {
    result += components[i] + delim;
  }
  return result;
}