from collections.abc import Iterable
from itertools import chain

from packaging.version import Version

from compreq.levels import Level


def ceil(level: Level, version: Version, keep_trailing_zeros: bool) -> Version:
    """Round a version up at a given level.

    In practice this means incrementing the value at the given level, and removing all following
    levels. For example::

        CeilLazyVersion.ceil(MAJOR, Version("1.2.3"), False) == Version("2")
        CeilLazyVersion.ceil(MINOR, Version("1.2.3"), False) == Version("1.3")

    Set `keep_trailing_zeros` to `True` to keep the trailing elements::

        CeilLazyVersion.ceil(MAJOR, Version("1.2.3"), True) == Version("2.0.0")
        CeilLazyVersion.ceil(MINOR, Version("1.2.3"), True) == Version("1.3.0")
    """
    release = version.release
    i = level.index(version)
    ceil_release: Iterable[int] = chain(release[:i], [release[i] + 1])
    if keep_trailing_zeros:
        ceil_release = chain(ceil_release, (0 for _ in release[i + 1 :]))
    return Version(f"{version.epoch}!" + ".".join(str(r) for r in ceil_release))


def floor(level: Level, version: Version, keep_trailing_zeros: bool) -> Version:
    """Round a version down at a given level.

    In practice this means removing all levels after the given one. For example::

        FloorLazyVersion.floor(MAJOR, Version("1.2.3"), False) == Version("1")
        FloorLazyVersion.floor(MINOR, Version("1.2.3"), False) == Version("1.2")

    Set `keep_trailing_zeros` to `True` to keep the trailing elements::

        FloorLazyVersion.floor(MAJOR, Version("1.2.3"), True) == Version("1.0.0")
        FloorLazyVersion.floor(MINOR, Version("1.2.3"), True) == Version("1.2.0")
    """
    release = version.release
    i = level.index(version)
    floor_release: Iterable[int] = release[: i + 1]
    if keep_trailing_zeros:
        floor_release = chain(floor_release, (0 for _ in release[i + 1 :]))
    return Version(f"{version.epoch}!" + ".".join(str(r) for r in floor_release))
