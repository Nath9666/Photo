import os
import sys

if len(sys.argv) > 1:
    name = sys.argv[1]
else:
    name = input("Enter directory name: ")

list_sub_directory = ["Export","Import", "ResolveProject"]

try:
    os.mkdir(name)
    for sub_directory in list_sub_directory:
        os.mkdir(os.path.join(name, sub_directory))
    print(f"Directory '{name}' created successfully.")
except FileExistsError:
    print(f"Directory '{name}' already exists.")

