## Internal System Stuff
- [ ] Stop using system binaries to setup the machine. Instead, there should be internal functions for handling these function


## FS
- [ ] Use (not yet implemented) internal functions to handle the `setup_dir` functions in the `StandardFS.init()` function instead of making them manually (stupid)


## Users/Groups
- [ ] Store the real and effective gid in the session class (because rn, group perms aren't checked)

## Libraries
### stdlib.h
- [ ] getenv
- [ ] setenv
- [ ] unsetenv


## Binaries
- [ ] Stop relying on other binaries (like `adduser` calls the `cp` and `chmod` binary to create the new user's home folder)
- [ ] Use Argparse for **all** binaries rather than *some*
- [ ] Use system libraries and **ONLY** system libraries for doing stuff related to the fs and system (no way to enforce this lol)

## Syscalls
- [x] read (read content from a file)
- [x] write (write data to a file)
- [x] stat (get stats about a file)
- [x] access (check if a file exists or check permissions on a file)
- [x] getcwd (get pathname of current working directory)
- [x] chdir (change current directory)
- [ ] rename (move a file)
- [x] mkdir (make a directory)
- [ ] rmdir (remove a directory)
- [x] chmod (change directory/file permissons)
- [x] chown (change owner/group owner of file/directory)
- [x] gettimeofday (get time of day in seconds)
- [x] getuid (get current effective UID)
- [x] setuid (set current effective UID)
- [x] getgid (get current effective group ID)
- [ ] setgid (set current effective group ID)
- [ ] reboot (reboot/shutdown the machine)
- [x] sethostname (set the system hostname)
- [x] gethostname (get the system hostname)
- [ ] execv (execute an executable directly / just check if it exists then run it)
- [ ] execvp (execute a command by checking path (what the shell does))

MAYBE:
- [ ] link (create a link to a file/directory)
- [ ] symlink (same as link, but we don't use inodes (because we don't have a real fs lol))
- [ ] unlink (delete a link or a file/directory)
- [ ] readlink (get the location of the file a link links to)

## Installable
- [ ] Find a way to handle package versions

## Misc
- [x] Change `SysCallStatus` to something else (maybe `Result` or `Response`)
- [x] Also change `SysCallMessages` to something else like `ResultMessage` or `ResponseMessage`