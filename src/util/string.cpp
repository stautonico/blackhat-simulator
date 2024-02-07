#include <util/string.h>

#include <string>
#include <vector>

std::vector<std::string> split(std::string str, char delim) {
    std::vector<std::string> result;
    std::string current = "";
    for (char c: str) {
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

std::string join(std::vector<std::string> components, char delim) {
    std::string result = "";
    for (auto i: components)
        result += i + delim;

    return result;
}

std::string erase(std::string str, std::string substr) {
    // Remove all instances of substr from str
    std::string result;
    for (int i = 0; i < str.size(); i++) {
        if (str.substr(i, substr.size()) == substr) {
            i += substr.size() - 1;
        } else {
            result += str[i];
        }
    }
    return result;
}
std::string strip_mount_point(std::string path, std::string mount_point) {
    {
        if (mount_point == path.substr(0, mount_point.length()))
            path.erase(0, mount_point.length());

        // Make sure we still have a '/' at the beginning
        if (path.substr(0, 1) != "/")
            path = "/" + path;

        return path;
    }
}
