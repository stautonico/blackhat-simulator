try:
    import os
    import re

    current_dir = os.getcwd()

    if current_dir.endswith("/tests"):
        binaries = [x.replace(".py", "") for x in os.listdir("../bin") if (x.endswith(".py") and x != "__init__.py")]

        with open("./test_binaries.py", "r") as f:
            content = f.read().split("\n")

    else:
        binaries = [x.replace(".py", "") for x in os.listdir("./client/blackhat/bin") if
                    (x.endswith(".py") and x != "__init__.py")]
        with open("./client/blackhat/tests/test_binaries.py", "r") as f:
            content = f.read().split("\n")

    binaries_with_tests = []

    for line in content:
        result = re.findall("(def )(test_)([\w\s]+)", line)
        if len(result) > 0:
            binaries_with_tests.append(result[0][2])

    binaries_without_tests = []

    for binary in binaries:
        if binary not in binaries_with_tests:
            binaries_without_tests.append(binary)

    print("These 'included' binaries do not have tests: ")

    for binary in binaries_without_tests:
        print(binary)
except Exception as e:
    print("Something went wrong while trying to find tests without binaries")
    print(e)
