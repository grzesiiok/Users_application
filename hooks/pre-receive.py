#!/usr/bin/python
import subprocess, re, sys


def val1():
    branch_regex = r"(major|feature|bugfix|hotfix)/*"
    branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("ascii").strip()
    if re.search(branch_regex, branch_name):
        print("[INFO] Branch validated!")
        sys.exit(0)
    else:
        print(f"[ERROR] Invalid branch name. Follow regex: {branch_regex}")
        sys.exit(1)

def val2():
    regex = r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(\(([\w\-.]+)\))?(!)?: ([\w ])+([\s\S]*)"
    def get_commit_msg():
        com = sys.argv[1]
        with open(com, "r+") as file:
            commit_msg = file.read()
            return commit_msg

    if re.search(regex, get_commit_msg()):
        print("[INFO] Commit validated!")
        sys.exit(0)
    else:
        print(f"[ERROR] Invalid Commit msq. Follow regex: {regex}")
        sys.exit(1)


val1()
val2()