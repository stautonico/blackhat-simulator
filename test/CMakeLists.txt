find_package(GTest REQUIRED)

add_executable(test-blackhat test.cpp)
target_link_libraries(test-blackhat PRIVATE blackhat-lib GTest::GTest GTest::Main)


add_test(
        NAME test-blackhat
        COMMAND test-blackhat
)