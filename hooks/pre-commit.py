#!/usr/bin/python
import subprocess, re, sys

branch_regex = r"(major|feature|bugfix|hotfix)/*"
branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("ascii").strip()

if re.search(branch_regex, branch_name):
    print("[INFO] Branch validated!")
    sys.exit(0)
else:
    print(f"[ERROR] Invalid branch name. Follow regex: {branch_regex}")
    sys.exit(1)
