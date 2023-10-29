#include <gtest/gtest.h>
#include <blackhat/computer.h>

TEST(TestComputer, lsWorks) {
    Blackhat::Computer c;
    auto result = c._readdir("/");
    EXPECT_EQ(result.size(), 11);
}