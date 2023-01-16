import sys
import os
import pathlib

d = str(pathlib.Path(__file__).parent.resolve()) + os.sep
sys.path.insert(0, str(pathlib.Path(__file__).parent.joinpath("../src").resolve()))
# ------------------------------------------------------
# Example
from pathtyped import (
    ResourceManager,
    DefinitionFile,
    Loaders,
    group_by,
    remove_known_extensions,
)

from resource_definition import root

rm = ResourceManager(
    f"{d}resources",
    DefinitionFile("", f"{d}resource_definition.py"),
    [remove_known_extensions(r"txt|json"), group_by(r"(speech)_(\d)")],
    [Loaders.text, Loaders.json],
)

resource: root = rm.root  # type: ignore

print(resource.data)
print(resource.main)

for line in resource.speech:
    print(line)
