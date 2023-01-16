from collections import defaultdict
import re

from .lib import (
    EntryDict,
    EntryList,
    EntryTree,
    middleware,
    ResourceManager,
)


def remove_known_extensions(extensions: str):
    """
    Creates a middleware that removes known extensions from keys

    ## Example
    ```py
    middlewares = [
        # Will transform file.txt to file
        remove_known_extensions(r"txt|mp3")
    ]
    ```
    """

    @middleware
    def mid(r: ResourceManager, loc: str, mapping: EntryTree) -> None:
        if isinstance(mapping, dict):
            for k in list(mapping.keys()):
                res = re.fullmatch(r"(.+)\.([^\.]+)", k)
                if res is None:
                    continue

                name, ext = res.groups()

                if re.fullmatch(extensions, ext):
                    if name in mapping:
                        r.warning(
                            f"{loc}: Duplicate key "
                            + repr(name)
                            + ": "
                            + repr(mapping[name])
                        )
                    mapping[name] = mapping.pop(k)

    return mid


def reducer(
    r: ResourceManager,
    entries: list[tuple[list[str | int | None], object]],
    keyname: str | int,
) -> object:
    if len(entries) == 0:
        return None
    if len(entries[0][0]) == 0:
        if len(entries) > 1:
            r.warning(f"Multiple entries for keyname {repr(keyname)}")
            for o in entries[1:]:
                r.warning(f"Ignoring: " + repr(o[1]))
        return entries[0][1]

    # Check if dict or list
    if isinstance(entries[0][0][0], str):
        # Use dict
        dstr: dict[str, list[tuple[list[str | int | None], object]]] = defaultdict(list)
        for path, o in entries:
            key = path[0]
            if key is None:
                r.warning(f"Key was None. Ignoring " + repr(o))
                continue
            if isinstance(key, int):
                r.warning(
                    f"Key {key} was an int when others were string. Ignoring " + repr(o)
                )
                continue

            dstr[key].append((path[1:], o))

        # Convert the dict
        return EntryDict({k: reducer(r, v, f"{keyname}.{k}") for k, v in dstr.items()})  # type: ignore
    else:
        assert isinstance(entries[0][0][0], int)
        # Use intermidiate dict
        dint: dict[int, list[tuple[list[str | int | None], object]]] = defaultdict(list)
        for path, o in entries:
            key = path[0]
            if key is None:
                r.warning(f"Key was None. Ignoring " + repr(o))
                continue
            if isinstance(key, str):
                r.warning(
                    f"Key {key} was a string when others were int. Ignoring " + repr(o)
                )
                continue

            dint[key].append((path[1:], o))

        # Convert the dict to list
        l: EntryList[object] = EntryList([None] * (max(dint.keys()) + 1))
        for k, v in dint.items():
            l[k] = reducer(r, v, f"{keyname}[{k}]")  # type: ignore

        return l


def entry_to_int_if_needed(e: str | None) -> str | int | None:
    if e is None:
        return None
    if e.isnumeric():
        return int(e)
    return e


def group_by(p: str):
    @middleware
    def grouper(r: ResourceManager, loc: str, mapping: EntryTree) -> EntryTree | None:
        if isinstance(mapping, EntryDict):
            rem: dict[str, object] = {}

            # Apply key transform

            ls: list[tuple[list[str | int | None], object]] = []
            for key, o in mapping.items():
                if (m := re.fullmatch(p, key)) is not None:
                    ls.append(
                        (
                            [
                                m.group(1),
                                *[entry_to_int_if_needed(e) for e in m.groups()[1:]],
                            ],
                            o,
                        )
                    )
                    continue
                rem[key] = o

            # TODO add some grid checks that enforces consistent grids
            # ex) [[0, 1], [0, 1, 2]] is not allowed as its neither a 2x2 grid or 2x3 grid
            # We know that this will return EntryTree as
            # the path is not empty

            res: EntryDict[object] = reducer(r, ls, loc)  # type: ignore
            if res:
                r.info(f"Found {len(ls)} entries for {loc}")
                res.update(rem)
                return res  # type: ignore

    return grouper


__all__ = [
    "remove_known_extensions",
    "group_by",
]
