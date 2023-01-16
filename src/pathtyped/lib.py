import functools
import os, hashlib, re, logging, inspect

from datetime import datetime
from pathlib import Path
import textwrap
from typing import (
    Any,
    Callable,
    Generator,
    Iterable,
    NamedTuple,
    Optional,
    Type,
    TypeGuard,
    TypeVar,
    Union,
    ParamSpec,
    overload,
)
from collections import namedtuple

T = TypeVar("T")
K = TypeVar("K")
R = TypeVar("R")
V = TypeVar("V", covariant=True)
P = ParamSpec("P")

# Force mark as covariant
class EntryDict(dict[str, V]):  # type: ignore
    pass


# Force mark as covariant
class EntryList(list[V]):  # type: ignore
    pass


def is_entry_node(
    entry_dict_or_list: object,
) -> TypeGuard[EntryDict[object] | EntryList[object]]:
    return isinstance(entry_dict_or_list, (EntryDict, EntryList))


# Each type represents a state
# Initial path scanning generates
MappingTypeDictOnly = EntryDict[Union[Path, "MappingTypeDictOnly"]]
# Middlewares process
MappingType = (
    # Simulate covariance
    EntryList[Union[Path, "MappingType"]]
    | EntryDict[Union[Path, "MappingType"]]
)

# Loaders parse
EntryTree = EntryList[object] | EntryDict[object]


class ResourceManagerConfig:
    def __init__(
        self,
        name: str = "ResourceManager",
        indent: str = "    ",
        ignore: str = "__.*__",
        logger: Optional[logging.Logger] = None,
        level: Optional[int] = None,
    ):
        """
        If `logger` is not provided, a default logger with `level` will be created
        """
        if logger is None:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO if level is None else level)
        else:
            if level is not None:
                logger.warn("Both logger and level are provided. Ignoring level")

        self.name = name
        self.indent = indent
        self.ignore = ignore
        self.logger = logger


class DefinitionFile:
    def __init__(self, default_import_statement: str, definition_file: str | Path):
        """
        `default_import_statement`: The import statement that will be used to import types from the definition file
        `definition_file`: The path to the definition file

        ## Example
        ```py
        d = DefinitionFile("from .types import *", "definition.py")
        ```
        """
        self.default_import_statement = default_import_statement
        self.definition_file = definition_file

    def write(self, integrity: str, content: str) -> None:
        """
        Check if the definition file exists before calling
        """
        with open(self.definition_file, "w") as f:
            f.write(
                textwrap.dedent(
                    # TODO Add more generics
                    f"""\
                    # {integrity}
                    # Automatically generated by ResourceManager at: {datetime.now()}
                    # DO NOT EDIT THIS FILE MANUALLY. 
                    # If you want to regenerate this file, change the integrity hash in the first line to something else
                    
                    # Some generic fixes
                    list = list[object]
                    dict = dict[object, object]

                    # Default import statement:
                    """
                )
                + f"{self.default_import_statement}\n# Main content:\n{content}"
            )

    def exists(self) -> bool:
        """
        Returns True if the definition file exists
        """
        return os.path.exists(self.definition_file)

    def read_integrity(self) -> str:
        """
        Returns an empty string if the definition file does not exist
        """
        if not self.exists():
            return ""
        with open(self.definition_file, "r") as f:
            return f.readline()[2:].strip()


def get_values(o: dict[Any, T] | list[T]) -> list[T]:
    if isinstance(o, dict):
        return list(o.values())
    return o


def create_blank_namedtuple(name: str, fields: Iterable[str]) -> NamedTuple:
    return namedtuple(name, fields)(**{f: None for f in fields})  # type: ignore


def _i_know_this_is_namedtuple(o: object) -> TypeGuard[NamedTuple]:
    return True


def _i_know_this_is_list(o: object) -> TypeGuard[list[Any]]:
    return True


class ResourceManager:
    def __init__(
        self,
        resource_folder: str | Path,
        definition_file: DefinitionFile,
        middlewares: list[Callable[["ResourceManager", str, EntryTree], EntryTree]],
        loaders: list[Callable[["ResourceManager", Any], Any]],
        config: Optional[ResourceManagerConfig] = None,
    ):
        self.resource_folder = resource_folder
        self.definition_file = definition_file
        self.middlewares = middlewares
        self.loaders = loaders
        self.config = ResourceManagerConfig() if config is None else config

        self.unified_directory_mappping = self._create_unified_directory_mapping(
            self.resource_folder
        )

        tree: EntryTree = self.unified_directory_mappping

        for middleware in self.middlewares:
            tree = middleware(self, "<root>", tree)

        # Make sure all properties are valid python property names
        tree = to_python_property_name(self, "<root>", tree)

        self.entry_tree = tree

        # Generate hash for integrity check
        hash_sum = hashlib.md5()
        for v in self.yield_consistent_hashables(self.entry_tree):
            hash_sum.update(v.encode())
        checksum = str(hash_sum.hexdigest())

        regenerate = False
        if self.definition_file.exists():
            if self.definition_file.read_integrity() != checksum:
                self.info(
                    "Folder contents/loaders have changed. Regenerating definition file"
                )
                regenerate = True
        else:
            self.info("Definition file does not exist. Regenerating definition file")
            regenerate = True

        # Process all loaders
        content = 'from typing import NamedTuple\n\nroot = NamedTuple("root", [\n'

        assert isinstance(self.entry_tree, EntryDict)

        def func(obj: object, location: str) -> object:
            for loader in self.loaders:
                try:
                    if (r := loader(self, obj)) is not None:
                        return r
                except Exception as e:
                    self.critical(
                        f"Error while loading object at location {location}; "
                        + repr(obj),
                        exc_info=True,
                    )
                    raise e
            self.warning(
                f"No loader found for object at location: {location}; " + repr(obj)
            )
            return obj

        def traverse_tree_generate_namedtuple_or_tuple(
            indent: str,
            nt: Union[NamedTuple, list[object]],
            m: EntryTree,
            location: str,
        ) -> Union[NamedTuple, list[object]]:
            nonlocal content
            if isinstance(m, EntryDict):
                assert _i_know_this_is_namedtuple(nt)
                for k, v in m.items():
                    content += f'{indent}("{k}", '
                    if isinstance(v, EntryDict):
                        # Is dict
                        d: dict[str, object] = v
                        content += f'NamedTuple("{k}", [\n'
                        rd = traverse_tree_generate_namedtuple_or_tuple(
                            indent + self.config.indent,
                            create_blank_namedtuple(k, d.keys()),
                            d,
                            location + "." + k,
                        )
                        nt = nt._replace(**{k: rd})
                        content += f"{indent}])"
                    elif isinstance(v, EntryList):
                        # Is list
                        l: list[object] = v
                        content += f"tuple[\n"
                        rl: list[
                            EntryTree
                        ] = traverse_tree_generate_namedtuple_or_tuple(
                            indent + self.config.indent,
                            [None for _ in range(len(l))],  # type: ignore
                            l,
                            location + "." + k,
                        )

                        # Cast back to tuple
                        nt = nt._replace(**{k: tuple(rl)})
                        content += f"{indent}],"
                    else:
                        # Is type
                        r = func(v, location) if v is not None else None
                        content += f'{type(r).__name__ if r is not None else "None"}'
                        nt = nt._replace(**{k: r})
                    content += f"),\n"
            else:
                assert isinstance(m, EntryList)
                assert _i_know_this_is_list(nt)
                for i, v in enumerate(m):
                    if isinstance(v, EntryDict):
                        # Is dict
                        d: dict[str, object] = v
                        content += f'{indent}NamedTuple("{i}", [\n'
                        rd = traverse_tree_generate_namedtuple_or_tuple(
                            indent + self.config.indent,
                            create_blank_namedtuple(str(i), d.keys()),
                            d,
                            location + "." + str(i),
                        )
                        nt[i] = rd
                        content += f"{indent}]),\n"
                    elif isinstance(v, EntryList):
                        # Is list
                        l: list[object] = v
                        content += f"{indent}tuple[\n"
                        rl = traverse_tree_generate_namedtuple_or_tuple(
                            indent + self.config.indent,
                            [None for _ in range(len(l))],  # type: ignore
                            l,
                            location + "." + str(i),
                        )
                        nt[i] = tuple(rl)
                        content += f"{indent}]"
                    else:
                        # Is type
                        r = func(v, location) if v is not None else None
                        content += (
                            f'{indent}{type(r).__name__ if r is not None else "None"}'
                        )
                        nt[i] = r
                    content += f",\n"
            return nt

        self.root: NamedTuple = traverse_tree_generate_namedtuple_or_tuple(
            self.config.indent,
            namedtuple("root", self.entry_tree.keys())(**self.entry_tree),  # type: ignore
            self.entry_tree,
            "root",
        )

        content += "])\n"

        if regenerate:
            self.definition_file.write(checksum, content)
            self.info("Definition file has been regenerated")
        else:
            self.info("Definition file is up to date")

    def _create_unified_directory_mapping(
        self, path: str | Path
    ) -> MappingTypeDictOnly:
        """
        Returns a dictionary that maps the path to the file or directory.

        This is an internal api
        """

        self.debug("Creating unified directory mapping")

        def recursive_mapper(
            path: str | Path, unified_part: MappingTypeDictOnly
        ) -> MappingTypeDictOnly:
            n = next(os.walk(path), None)
            if n is None:
                raise FileNotFoundError(f"Path {path} does not exist")
            root, dirs, files = n
            for file in files:
                if self.config.ignore and re.fullmatch(self.config.ignore, file):
                    continue
                f = unified_part[file] = Path(os.path.join(root, file))

                self.debug(f"{f.resolve()} has been added to unified directory mapping")

            for dir in dirs:
                if self.config.ignore and re.fullmatch(self.config.ignore, dir):
                    continue

                ds = os.path.join(root, dir)
                # Create folder
                d = unified_part[dir] = recursive_mapper(ds, EntryDict())

                self.debug(f"Traversing {ds}")
                recursive_mapper(os.path.join(root, dir), d)
            return unified_part

        return recursive_mapper(path, EntryDict())

    def yield_consistent_hashables(self, value: object) -> Generator[str, None, None]:
        """
        Yields a consistent hashable representation of the tree
        """
        if isinstance(value, dict):
            yield from value.keys()
            for v in value.values():
                v: object
                yield from self.yield_consistent_hashables(v)
        elif isinstance(value, list):
            for v in value:
                v: object
                yield from self.yield_consistent_hashables(v)
        elif isinstance(value, Path):
            yield from value.parts
        else:
            # We are out of options. Yield the type
            yield type(value).__name__

    @property
    def critical(self):
        return self.config.logger.critical

    @property
    def error(self):
        return self.config.logger.error

    @property
    def warning(self):
        return self.config.logger.warning

    @property
    def info(self):
        return self.config.logger.info

    @property
    def debug(self):
        return self.config.logger.debug


def _walk_stems(
    tree: EntryTree, location: str
) -> Generator[
    tuple[EntryList[object], str, Generator[int, None, None]], None, None
] | Generator[tuple[EntryDict[object], str, Generator[str, None, None]], None, None]:
    """
    yields root, property pair and allows transformation of the object itself

    Best to call with `[object_to_call]` and access [0] (fake head)

    All keys are guaranteed to return `EntryList` or `EntryDict

    This is an internal api
    """

    if isinstance(tree, EntryDict):
        keys = tree.keys()
        yield tree, location, (k for k in keys if is_entry_node(tree[k]))

        for k, v in tree.items():
            if is_entry_node(v):
                yield from _walk_stems(v, f"{location}.{k}" if location else k)
    else:
        indices = range(len(tree))
        yield tree, location, (i for i in indices if is_entry_node(tree[i]))

        for i, v in enumerate(tree):
            if is_entry_node(v):
                yield from _walk_stems(v, f"{location}[{i}]" if location else f"[{i}]")


def middleware(func: Callable[[ResourceManager, str, EntryTree], Optional[EntryTree]]):
    """
    Decorator for middlewares
    """

    @functools.wraps(func)
    def wrapper(self: ResourceManager, location: str, tree: EntryTree) -> EntryTree:
        fake_head: EntryTree = EntryDict({"<root>": tree})
        for root, location, properties in _walk_stems(fake_head, ""):
            for property in properties:
                if isinstance(root, EntryDict):
                    assert isinstance(property, str)

                    head = root[property]
                    assert is_entry_node(head)

                    r = func(self, f"{location}.{property}", head)
                    if r is not None:
                        root[property] = r
                else:
                    assert isinstance(root, EntryList)
                    assert isinstance(property, int)

                    head = root[property]
                    assert is_entry_node(head)

                    r = func(self, f"{location}.{property}", head)
                    if r is not None:
                        root[property] = r

        h = fake_head.get("<root>")
        assert is_entry_node(h)
        return h

    return wrapper


def _normalize_property_name(r: ResourceManager, loc: str, name: str) -> str:
    # Replace all leading underscores
    s = re.sub(r"^_+", "", name)
    # Replace all non-alphanumeric characters with underscores
    s = re.sub(r"[^a-zA-Z0-9_]", "_", s)
    if s[0].isdigit():
        r.warning(
            f"Property name starts with a digit at {repr(loc)}. Adding index_ prefix"
        )
        s = "index_" + s
    return s


@middleware
def to_python_property_name(
    r: ResourceManager, loc: str, tree: EntryTree
) -> Optional[EntryTree]:
    """
    Converts all keys into python property name
    """
    r.debug(f"to_property_name: Checking {loc}")
    if isinstance(tree, dict):

        def con(k: str) -> str:
            res = _normalize_property_name(r, loc, k)
            if res != k:
                r.debug(f"Renamed {loc}.{k} -> {loc}.{res}")
            return res

        return EntryDict({con(k): v for k, v in tree.items()})


@overload
def loader(
    accept_or_func: Callable[[ResourceManager, Path], R]
) -> Callable[[ResourceManager, Any], Optional[R]]:
    pass


@overload
def loader() -> Callable[
    [Callable[[ResourceManager, Path], R]],
    Callable[[ResourceManager, Any], Optional[R]],
]:
    pass


@overload
def loader(
    accept_or_func: Type[T],
) -> Callable[
    [Callable[[ResourceManager, T], R]], Callable[[ResourceManager, Any], Optional[R]]
]:
    pass


def loader(
    accept_or_func: Callable[[ResourceManager, Path], R] | Type[T] = Path
) -> Callable[[ResourceManager, Path], Optional[R]] | Callable[
    [Callable[[ResourceManager, T], R]], Callable[[ResourceManager, Any], Optional[R]]
]:
    """
    Decorator for loaders
    """
    if not inspect.isclass(accept_or_func):

        @functools.wraps(accept_or_func)
        def wrapper(self: ResourceManager, arg: Any) -> Optional[R]:
            if isinstance(arg, Path):
                # too hard to fix
                return accept_or_func(self, arg)  # type: ignore
            return None

        return wrapper

    def internal_loader(
        func: Callable[[ResourceManager, T], R]
    ) -> Callable[[ResourceManager, Any], Optional[R]]:
        @functools.wraps(func)
        def wrapper(self: ResourceManager, arg: Any) -> Optional[R]:
            if isinstance(arg, accept_or_func):
                return func(self, arg)
            return None

        return wrapper

    return internal_loader


__all__ = [
    "EntryDict",
    "EntryList",
    "ResourceManager",
    "ResourceManagerConfig",
    "DefinitionFile",
    "is_entry_node",
]
