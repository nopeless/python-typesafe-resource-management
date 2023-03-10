# 727f97830786b604adfb9431d39bb6c6
# Automatically generated by ResourceManager at: 2023-01-16 00:54:46.615501
# DO NOT EDIT THIS FILE MANUALLY. 
# If you want to regenerate this file, change the integrity hash in the first line to something else

# Some generic fixes
list = list[object]
dict = dict[object, object]

# Default import statement:
from defaults import *
# Main content:
from typing import NamedTuple

root = NamedTuple("root", [
  ("audio", NamedTuple("audio", [
    ("bgm", NamedTuple("bgm", [
      ("underwater1", WindowsPath),
      ("underwater2", WindowsPath),
    ])),
    ("sfx", NamedTuple("sfx", [
      ("collect", WindowsPath),
      ("dash", WindowsPath),
      ("head", WindowsPath),
      ("jump", WindowsPath),
      ("land", WindowsPath),
    ])),
  ])),
  ("fonts", NamedTuple("fonts", [
    ("monogram", WindowsPath),
  ])),
  ("images", NamedTuple("images", [
    ("chests", NamedTuple("chests", [
      ("big_chest", WindowsPath),
      ("small_chest", WindowsPath),
      ("small_chest_open", WindowsPath),
    ])),
    ("cleaner", NamedTuple("cleaner", [
      ("sheet", WindowsPath),
    ])),
    ("npcs", NamedTuple("npcs", [
      ("npc1", WindowsPath),
      ("npc2", WindowsPath),
      ("npc3", WindowsPath),
    ])),
    ("player", NamedTuple("player", [
      ("hitbox", WindowsPath),
      ("shee2t", WindowsPath),
      ("sheet", WindowsPath),
    ])),
    ("trash", NamedTuple("trash", [
      ("banana", WindowsPath),
      ("chum", WindowsPath),
      ("egg", WindowsPath),
      ("plasticrings", WindowsPath),
      ("sodacan", WindowsPath),
    ])),
    ("fallback", WindowsPath),
  ])),
  ("level", NamedTuple("level", [
    ("c1closed", WindowsPath),
    ("c2closed", WindowsPath),
    ("gypst1", WindowsPath),
    ("land", WindowsPath),
    ("landset", WindowsPath),
    ("longweed", WindowsPath),
    ("longweedset", WindowsPath),
    ("npc1", WindowsPath),
    ("npc2", WindowsPath),
    ("npc3", WindowsPath),
    ("skybox1", WindowsPath),
    ("skyboxset", WindowsPath),
    ("tropics", WindowsPath),
    ("under", WindowsPath),
    ("underset", WindowsPath),
    ("water", WindowsPath),
    ("waterset", WindowsPath),
  ])),
  ("mod", NamedTuple("mod", [
    ("init__", WindowsPath),
  ])),
  ("tiles", NamedTuple("tiles", [
    ("grass", tuple[
      tuple[
        str,
        str,
      ],
      tuple[
        str,
        str,
      ],
      tuple[
        str,
        str,
        str,
      ],
      tuple[
        str,
        str,
        str,
      ],
    ],),
  ])),
  ("root", WindowsPath),
  ("script", str),
])
