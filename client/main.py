from blackhat.computer import Computer

comp = Computer()

comp.add_user("steve", "password")


hostname_file_lookup = comp.fs.find("/etc/hostname")

if hostname_file_lookup.success:
    hostname_file = hostname_file_lookup.data
    print(hostname_file.pwd())
    print(f"Original hostname: {comp.hostname}")

    hostname_file.content = "testserver"

    print(f"/etc/hostname changed but not updated: {comp.hostname}")
    comp.update_hostname()
    print(f"/etc/hostname changed and updated: {comp.hostname}")

    hostname_file.delete(0)

    comp.update_hostname()
    print(f"/etc/hostname deleted and updated: {comp.hostname}")

else:
    print(f"Unable to find hostname file!")




for uid, user in comp.users.items():
    print(f"UID: {uid} - Username: {user.username} - Password: {user.password}")
