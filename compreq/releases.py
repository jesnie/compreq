from __future__ import annotations

from collections.abc import Collection, Iterator, Set
from dataclasses import dataclass, replace
from typing import Any

from packaging.version import Version

from compreq.time import UtcDatetime


@dataclass(order=True, frozen=True)
class Release:
    """A specific release of a given distribution."""

    distribution: str
    version: Version
    released_time: UtcDatetime
    successor: Release | None


@dataclass(frozen=True)
class ReleaseSet(Set[Release]):
    """A set of releases of the same distribution."""

    distribution: str
    releases: frozenset[Release]

    def __post_init__(self) -> None:
        assert all(r.distribution == self.distribution for r in self.releases), (
            f"Inconsistent distribution names in ReleaseSet. Found: {self}."
        )

    def __iter__(self) -> Iterator[Release]:
        return iter(self.releases)

    def __contains__(self, release: Any) -> bool:
        return release in self.releases

    def __len__(self) -> int:
        return len(self.releases)


def infer_successor(versions: Collection[Version]) -> dict[Version, Version | None]:
    """Given a collection of `Version`s, compute their successors."""
    next_main: Version | None = None
    next_pre: Version | None = None
    next_dev: Version | None = None
    result = {}
    for version in sorted(versions, reverse=True):
        if version.is_devrelease:
            result[version] = next_dev
            next_dev = version
        elif version.is_prerelease:
            result[version] = next_pre
            next_dev = next_pre = version
        else:
            result[version] = next_main
            next_main = next_pre = next_dev = version
    return result


def infer_and_set_successor(releases: ReleaseSet) -> ReleaseSet:
    """Compute and set the `successor` fields on a set of releases."""
    by_version = {r.version: r for r in releases}
    successors = infer_successor(by_version)
    for r in sorted(releases, reverse=True):
        s = successors.get(r.version)
        if s is not None:
            r = replace(r, successor=by_version[s])
        by_version[r.version] = r
    return ReleaseSet(distribution=releases.distribution, releases=frozenset(by_version.values()))
