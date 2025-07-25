from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final, TypeAlias

from packaging.version import Version


class Level(ABC):
    """Strategy for computing an index into a version tuple.

    For example for specyfing whether I want to refer to `1`, `2` or `4` in the version `1.2.4`.

    In semantic version, this is equivivalent to specifier whether you want the major, micro or
    bugfix version.
    """

    @abstractmethod
    def index(self, version: Version) -> int:
        """Compute the index into the version tuple."""


@dataclass(order=True, frozen=True)
class IntLevel(Level):
    """A `Level` that always picks the same element of the version."""

    level: int

    def index(self, version: Version) -> int:
        return self.level


@dataclass(order=True, frozen=True)
class RelativeToFirstNonZeroLevel(Level):
    """A `Level` that picks an element relative to the first non-zero element in the version tuple.

    For example::

        RelativeToFirstNonZeroLevel(1).index(Version("0.1.3")) = 2

    so, referring to the value `3`.
    """

    relative_level: int

    def __post_init__(self) -> None:
        assert self.relative_level >= 0

    def index(self, version: Version) -> int:
        for i, r in enumerate(version.release):
            if r != 0:
                return i + self.relative_level
        raise AssertionError(f"No non-zero segment found in {version}")


MAJOR: Final[Level] = IntLevel(0)
"""Pick the "major" version."""

MINOR: Final[Level] = IntLevel(1)
"""Pick the "minor" version."""

MICRO: Final[Level] = IntLevel(2)
"""Pick the "micro"/"bugfix" version."""

REL_MAJOR: Final[Level] = RelativeToFirstNonZeroLevel(0)
"""
Pick the first non-zero element.

In `0.0.1.2.3.4` this would pick `1`.
"""

REL_MINOR: Final[Level] = RelativeToFirstNonZeroLevel(1)
"""
Pick the element just after the first non-zero element.

In `0.0.1.2.3.4` this would pick `2`.
"""

REL_MICRO: Final[Level] = RelativeToFirstNonZeroLevel(3)
"""
Pick the second element after the first non-zero element.

In `0.0.1.2.3.4` this would pick `3`.
"""


AnyLevel: TypeAlias = int | Level
"""
Type alias for anything that can be converted to a `Level`.

Integers are interpreted as fixed indices.
"""


def get_level(level: AnyLevel) -> Level:
    """Get a `Level` for the given level-like value."""
    if isinstance(level, int):
        level = IntLevel(level)
    if isinstance(level, Level):
        return level
    raise AssertionError(f"Unknown type of level: {type(level)}")
