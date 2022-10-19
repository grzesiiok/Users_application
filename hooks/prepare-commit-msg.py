#!/usr/bin/python

regex = r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(\(([\w\-.]+)\))?(!)?: ([\w ])+([\s\S]*)"

print("Commit message template:")
print(f"{regex}")