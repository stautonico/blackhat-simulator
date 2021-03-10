from blackhat.computer import Computer

comp = Computer()

print(comp.users)
print(comp.parent)
print(comp.hostname)
print(comp.sessions)

comp.add_user("steve", "password")

print(comp.users)

print(comp.users["steve"].uid)
print(comp.users["steve"].username)
print(comp.users["steve"].password)

for filename, file in comp.fs.files.files.items():
    print(f"{filename} - {file.owner}")
    if filename == "var":
        for subfilename, subfile in file.files.items():
            print(f"\t{subfilename} - {subfile.owner}")
            if subfilename == "log":
                for subsubfilename, subsubfile in subfile.files.items():
                    print(f"\t\t{subsubfilename} - {subsubfile.owner}")