import sys
import os
import pathlib
import logging

d = str(pathlib.Path(__file__).parent.resolve()) + os.sep
sys.path.insert(0, str(pathlib.Path(__file__).parent.joinpath("../src").resolve()))
os.chdir(d)
# ^ Not needed
# ------------------------------------------------------
# Example code

from pathtyped import *

# For enabling debug
logging.basicConfig(level=logging.DEBUG)
rm = ResourceManager(
    f"resources",
    DefinitionFile("", f"resource_definition.py"),
    [remove_known_extensions(r"txt|json"), group_by(r"(speech)_(\d)")],
    [Loaders.text, Loaders.json],
    # For enabling debug
    ResourceManagerConfig(level=logging.DEBUG),
)

from resource_definition import root

resource: root = rm.root  # type: ignore

print(resource.data)
print(resource.main)

for line in resource.speech:
    print(line)
