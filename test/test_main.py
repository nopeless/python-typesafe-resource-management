import logging
from src.pathtyped import *
from definition import root

logging.basicConfig(level=logging.DEBUG)
r = ResourceManager(
    "test\\resources",
    DefinitionFile("from defaults import *", "test\\definition.py"),
    [remove_known_extensions(r".*"), group_by(r"(grass)(\d)(\d)")],
    [Loaders.text],
    ResourceManagerConfig(indent="  ", level=logging.DEBUG),
)

resources: root = r.root  # type: ignore


def test_entries():
    assert resources.audio is not None


def test_root():
    assert resources.root is not None
