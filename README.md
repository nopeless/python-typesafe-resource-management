# Typesafe resource management in Python

This package creates a definition file by traversing the resource folder and parsing the files

## Features
 - [x] Typesafe resource management (needs compatible type checker)
 - [x] Automatic type definition generation
 - [x] Middlewares, loaders api

PyPI: https://pypi.org/project/pathtyped/

```sh
pip install pathtyped
```

# Showcase

> This code can be found in [demo](demo)

## Your text files

```
resources/
    data.json
    main.txt
    speech_0.txt
    speech_1.txt
    speech_2.txt
```

```py
# main.py
from pathtyped import *

rm = ResourceManager(
    f"resources",
    DefinitionFile("", f"resource_definition.py"),
    [remove_known_extensions(r"txt|json"), group_by(r"(speech)_(\d)")],
    [Loaders.text, Loaders.json],
)

# The file below doesn't exist when starting
from resource_definition import root

resource: root = rm.root  # type: ignore
```

```py
# defaults.py
# No need to import anything since type str is already imported
# Example
from some_code import YourClass
```

### Generates

```py
# 8587d74aed20f794cdfc800f26c456b7
# Automatically generated by ResourceManager at: 2023-01-15 23:37:27.451164
# DO NOT EDIT THIS FILE MANUALLY. 
# If you want to regenerate this file, change the integrity hash in the first line to something else

# Some generic fixes
list = list[object]
dict = dict[object, object]

# Default import statement:

# Main content:
from typing import NamedTuple

root = NamedTuple("root", [
    ("speech", tuple[
        str,
        str,
        str,
    ],),
    ("data", dict),
    ("main", str),
])
```

## And provides you with type compilation

![1673847586091](https://raw.githubusercontent.com/nopeless/python-typesafe-resource-management/main/image/README/1673847586091.png)

# Documentation

## Middlewares

Middlewares are functions that have the ability to modify the tree structure itself as well as change the value of the nodes

They are applied in the order they are passed to the ResourceManager, with each middleware doing a full DFS preorder traversal of the tree

```py
for middleware in middlewares:
    # The @middleware decorator will initiate the dfs preorder traversal
    tree = middleware(self, "<root>", tree)
```
<img src="https://github.com/nopeless/python-typesafe-resource-management/raw/main/image/README/1673837228765.png" alt="drawing" width="200"/>

This also means that the middleware will be applied to the leaf of the trees that it has returned. This is the most desirable behavior for applying middlewares

```py
@middleware
def strip_numbers_in_string(r: ResourceManager, location: str, tree: EntryTree) -> Optional[EntryTree]:
    """Removes all number property from tree"""
    if isinstance(tree, EntryDict):
        new_tree = EntryDict()
        for key in list(tree.keys()):
            n = re.sub(r"\d+", "", key)
            new_tree[n] = tree[key]
        # If a new dict or list is returned, it will replace the old one
        # Be sure to return a new EntryTree
        return new_tree
    # Returning None indicates that the tree should not be changed
    # You can also modify tree in place and it will be reflected
    return None
```

## Loaders

Loaders are simpler middlewares. They are functions that only take the leaf node and transform it into a useful value.

Most leaf nodes are `Path` objects

The resource manager will attempt to apply each loader to the leaf node in the order they are passed to the ResourceManager. Returning `None` indicates that the loader does not know how to handle the leaf node and will pass it to the next loader

```py
for loader in self.loaders:
    if (r := loader(self, obj)) is not None:
        obj = r
```

This means that a loader that transforms from `A->B` will be handled by another loader that transforms from `B-C` if they are in order

```py
# Basic loaders
@loader
def return_suffix(r: ResourceManager, path: Path) -> str:
    return path.suffix

@loader
@extension("mp3")
def pygame_load(r: ResourceManager, path: Path) -> pygame.mixer.Sound:
    return pygame.mixer.Sound(path)

fallback_image = pygame.image.load("fallback.png")

@loader
@extension(r"png|jpg|jpeg")
@fallback(fallback_image) # If the loading raises an Exception
def pygame_image_load(r: ResourceManager, path: Path) -> pygame.Surface:
    return pygame.image.load(path)

# Advanced loaders

# Loader that accepts certain object nodes
# Requires a compatible middleware to generate such leaves
@loader(Script)
def execute(r: ResourceManager, s: Script) -> object:
    return s.execute()

```

# FAQ

## Visual Studio Code shows that the type is any

Change the `python.analysis.typeCheckingMode` setting to `strict` and it not allow you to access invalid properties. Make sure that the Python language server is Pylance

```json
{
    "python.analysis.typeCheckingMode": "strict"
}
```

## Cannot import `TypeGuard`

Project requires Python 3.10 or higher

# Contributing

If you have an idea for this library, please make an issue first instead of a PR. I will be happy to discuss it with you
