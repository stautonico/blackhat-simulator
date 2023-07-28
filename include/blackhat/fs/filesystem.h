#pragma once

#include <string>

namespace Blackhat{
// Template class that all filesystems should inherit from

/* A filesystem NEEDS to implement the following functions (taken from FUSE)
 * (https://developer.ibm.com/articles/l-fuse/)
int (getattr) (const char , struct stat );
int (readlink) (const char , char , size_t);
int (getdir) (const char , fuse_dirh_t, fuse_dirfil_t);
int (mknod) (const char , mode_t, dev_t);
int (mkdir) (const char , mode_t);
int (unlink) (const char );
int (rmdir) (const char );
int (symlink) (const char , const char );
int (rename) (const char , const char );
int (link) (const char , const char );
int (chmod) (const char , mode_t);
int (chown) (const char , uid_t, gid_t);
int (truncate) (const char , off_t);
int (utime) (const char , struct utimbuf );
int (open) (const char , struct fuse_file_info );
int (read) (const char , char , size_t, off_t, struct fuse_file_info );
int (write) (const char , const char , size_t, off_t,struct fuse_file_info );
int (statfs) (const char , struct statfs );
int (flush) (const char , struct fuse_file_info );
int (release) (const char , struct fuse_file_info );
int (fsync) (const char , int, struct fuse_file_info );
int (setxattr) (const char , const char , const char , size_t, int);
int (getxattr) (const char , const char , char , size_t);
int (listxattr) (const char , char , size_t);
int (removexattr) (const char , const char *);
 */
class Filesystem {
public:
  Filesystem() = default;

  virtual int create(std::string path, int uid, int gid, int mode) = 0;

  virtual std::string read(std::string path) = 0;

  virtual int write(std::string path, std::string data) = 0;

  virtual int mv(std::string path, std::string new_path) = 0;

  virtual int chmod(std::string path, int mode) = 0;

  virtual int chown(std::string path, int uid, int gid) = 0;

  virtual int rm(std::string path) = 0;

private:
};
}