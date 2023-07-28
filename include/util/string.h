#pragma once

#include <string>
#include <vector>

std::vector<std::string> split(std::string str, char delim);

std::string join(std::vector<std::string> components, char delim, int start,
                 int end);