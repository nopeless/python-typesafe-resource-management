import functools
import json as jsonlib
from pathlib import Path
import re
from typing import Callable, NamedTuple, Optional, TypeVar
from .lib import ResourceManager, loader

T = TypeVar("T")


def extension(ext: str):
    def ext_loader_decorator(
        func: Callable[[ResourceManager, Path], object]
    ) -> Callable[[ResourceManager, Path], object]:
        @functools.wraps(func)
        def wrapper(r: ResourceManager, p: Path):
            assert isinstance(p, Path)
            if re.fullmatch(ext, p.suffix[1:]):
                return func(r, p)

        return wrapper

    return ext_loader_decorator


P = TypeVar("P", contravariant=True)


def fallback(
    fallback_value: T,
) -> Callable[
    [Callable[[ResourceManager, P], Optional[T]]],
    Callable[[ResourceManager, P], Optional[T]],
]:
    def fallback_decorator(
        func: Callable[[ResourceManager, P], Optional[T]]
    ) -> Callable[[ResourceManager, P], Optional[T]]:
        @functools.wraps(func)
        def wrapper(r: ResourceManager, o: P):
            try:
                return func(r, o)
            except Exception as e:
                r.error(f"Failed to load {repr(o)}: {e}")
                return fallback_value

        return wrapper

    return fallback_decorator


@loader
@extension(r"txt")
@fallback("Cannot load text")
def text(r: ResourceManager, p: Path):
    r.debug("Loaded text from " + repr(p))
    return p.read_text()


@loader
@extension(r"json")
def json(r: ResourceManager, p: Path):
    r.debug("Loaded json from " + repr(p))
    return jsonlib.loads(p.read_text())


class Loaders(NamedTuple):
    text = text
    json = json


__all__ = ["extension", "fallback", "Loaders"]
