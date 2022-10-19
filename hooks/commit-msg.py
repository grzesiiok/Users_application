#!/usr/bin/python
import sys, re

com = sys.argv[1]
regex = r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(\(([\w\-.]+)\))?(!)?: ([\w ])+([\s\S]*)"

def get_commit_msg():
    with open(com, "r+") as file:
        commit_msg = file.read()
        return commit_msg

if re.search(regex, get_commit_msg()):
    print("[INFO] Commit validated!")
    sys.exit(0)
else:
    print(f"[ERROR] Invalid Commit msq. Follow regex: {regex}")
    sys.exit(1)