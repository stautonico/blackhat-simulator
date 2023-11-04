#pragma once

enum E {
    PERM   = 1, // Operation not permitted
    NOENT  = 2, // No such file or directory
    NOEXEC = 8, // Exec format error
    BADF   = 9, // Bad file descriptor
    EXIST  = 17, // File exists
};