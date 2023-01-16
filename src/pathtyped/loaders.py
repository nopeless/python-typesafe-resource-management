import functools
from pathlib import Path
import re
from typing import Callable, NamedTuple, TypeVar
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


def fallback(
    fallback_value: T,
) -> Callable[
    [Callable[[ResourceManager, T], object]], Callable[[ResourceManager, T], object]
]:
    def fallback_decorator(
        func: Callable[[ResourceManager, T], object]
    ) -> Callable[[ResourceManager, T], object]:
        @functools.wraps(func)
        def wrapper(r: ResourceManager, o: T):
            try:
                return func(r, o)
            except Exception as e:
                r.error(f"Failed to load {repr(o)}: {e}")
                return fallback_value

        return wrapper

    return fallback_decorator


@loader
@extension(r"txt")
def text(r: ResourceManager, o: object):
    if isinstance(o, Path):
        r.debug("Loaded text from " + repr(o))
        return o.read_text()


class Loaders(NamedTuple):
    text = text


__all__ = ["extension", "fallback", "Loaders"]
