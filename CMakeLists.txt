cmake_minimum_required(VERSION 3.25)
project(blackhat-simulator)

set(CMAKE_CXX_STANDARD 20)

include_directories(include)

# Recursively include all the headers
# (just for IDEs, not actually used by CMake)
file(GLOB_RECURSE HEADERS include/*.h)

# I really don't like putting all the sources all here, but it'll do for now ig
set(SOURCES
        src/blackhat/computer.cpp
        src/blackhat/interpreter.cpp
        src/blackhat/process.cpp

        src/blackhat/fs/ext4.cpp

        src/util/string.cpp
        )

# Add some settings for pocketpy
set(PK_USE_BOX2D OFF CACHE BOOL "Don't compile box2D")
set(PK_BUILD_STATIC_LIB ON CACHE BOOL "Compile the static library for pocketpy")
add_subdirectory(vendor/pocketpy)

include_directories(vendor/pocketpy/include)

add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS} src/main.cpp)

# Build and link nlohmann/json
# set(JSON_BuildTests OFF CACHE INTERAL "")
#add_subdirectory(vendor/nlohmann_json)

# add nlohmann_json::nlohmann_json'
target_link_libraries(${PROJECT_NAME} pocketpy)
