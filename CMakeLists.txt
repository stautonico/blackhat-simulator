cmake_minimum_required(VERSION 3.15)
project(blackhat-simulator)

set(CMAKE_CXX_STANDARD 17)


include_directories(include)

# Recursively include all the headers
# (just for IDEs, not actually used by CMake)
file(GLOB_RECURSE HEADERS include/*.h)

# I really don't like putting all the sources all here, but it'll do for now ig
set(SOURCES
        # blackhat/
        src/blackhat/computer.cpp
        src/blackhat/user.cpp
        src/blackhat/process.cpp

        src/blackhat/fs/ext4.cpp

        # util/
        src/util/crypto.cpp
        src/util/string.cpp
        src/util/time.cpp
        src/blackhat/interpreter.cpp)

add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS} src/main.cpp)

target_link_libraries(${PROJECT_NAME} duktape)