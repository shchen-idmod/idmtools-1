#!/usr/bin/env python
import glob
import shutil

import os
from os.path import abspath, join, dirname

base_directory = abspath(join(dirname(__file__), '..'))

stub_final = join(base_directory, "stub_out")
if os.path.exists(stub_final):
    shutil.rmtree(stub_final)

for file in glob.glob(join(base_directory, "**/*.pyi"), recursive=True):
    # ignore test files
    if "tests" not in file:
        with open(file, 'r') as interface_in:
            # skip first line to remove the data
            lines = interface_in.readlines()[1:]

        dest_path = file.replace(base_directory, stub_final)

        os.makedirs(dirname(dest_path), exist_ok=True)
        with open(dest_path, 'w') as interface_out:
            interface_out.write("\n".join(lines))

    os.remove(file)
