import datetime as dt
from collections.abc import AsyncIterator, Collection, Sequence
from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pytest import MonkeyPatch

import compreq as cr
from tests.utils import fake_release, fake_release_set, utc


def test_version() -> None:
    assert isinstance(cr.version, cr.VersionToken)
    assert isinstance(cr.v, cr.VersionToken)


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            cr.distribution("foo.bar"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.dist("foo.bar"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.url("http://path/v1.2.3"),
            cr.LazyRequirement(
                distribution=None,
                url="http://path/v1.2.3",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.specifier(">=1.2.3"),
            cr.get_lazy_specifier(">=1.2.3"),
        ),
        (
            cr.specifier_set(">=1.2.3,<2.0.0"),
            cr.get_lazy_specifier_set(">=1.2.3,<2.0.0"),
        ),
        (
            cr.marker("python_version=='1.2.3'"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=cr.get_marker("python_version=='1.2.3'"),
                optional=None,
            ),
        ),
        (
            cr.optional(),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=True,
            ),
        ),
    ],
)
def test_factories(requirement: cr.LazyRequirement, expected: cr.LazyRequirement) -> None:
    assert requirement == expected


def test_releases() -> None:
    assert cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet(None)) == cr.releases()
    assert cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet("foo.bar")) == cr.releases("foo.bar")


def test_prereleases() -> None:
    assert cr.PreLazyReleaseSet(cr.AllLazyReleaseSet(None)) == cr.prereleases()
    assert cr.PreLazyReleaseSet(cr.AllLazyReleaseSet("foo.bar")) == cr.prereleases("foo.bar")


def test_devreleases() -> None:
    assert cr.AllLazyReleaseSet(None) == cr.devreleases()
    assert cr.AllLazyReleaseSet("foo.bar") == cr.devreleases("foo.bar")


async def test_default_python() -> None:
    default_python = Version("3.11.4")
    context = MagicMock(cr.DistributionContext)
    context.default_python = default_python
    lazy = cr.default_python()
    assert default_python == await lazy.resolve(context)


async def test_python_specifier() -> None:
    python_specifier = SpecifierSet("<4,>=3.8")
    context = MagicMock(cr.DistributionContext)
    context.python_specifier = python_specifier
    lazy = cr.python_specifier()
    assert python_specifier == await lazy.resolve(context)


@pytest.mark.parametrize(
    "releases,expected",
    [
        (["1!1.0.0", "1.2.3", "1.2.3a1", "1.2.3a1dev1", "1.2.2"], "1.2.2"),
        (["1!1.0.0", "1.2.3", "1.2.3a1", "1.2.3a1dev1"], "1.2.3a1dev1"),
        (["1!1.0.0", "1.2.3", "1.2.3a1"], "1.2.3a1"),
        (["1!1.0.0", "1.2.3"], "1.2.3"),
        (["1!1.0.0"], "1!1.0.0"),
    ],
)
async def test_min_ver(releases: Collection[str], expected: str) -> None:
    release_set = fake_release_set(releases=releases, infer_successors=False)
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    min_ver = cr.min_ver(release_set)
    assert min_ver.get_distribution() == "foo.bar"
    assert fake_release(version=expected) == await min_ver.resolve(context)


@pytest.mark.parametrize(
    "releases,expected",
    [
        (["1!1.0.0", "1.2.3", "1.2.3a1", "1.2.3a1dev1", "1.2.2"], "1!1.0.0"),
        (["1.2.3", "1.2.3a1", "1.2.3a1dev1", "1.2.2"], "1.2.3"),
        (["1.2.3a1", "1.2.3a1dev1", "1.2.2"], "1.2.3a1"),
        (["1.2.3a1dev1", "1.2.2"], "1.2.3a1dev1"),
        (["1.2.2"], "1.2.2"),
    ],
)
async def test_max_ver(releases: Collection[str], expected: str) -> None:
    release_set = fake_release_set(releases=releases, infer_successors=False)
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    max_ver = cr.max_ver(release_set)
    assert max_ver.get_distribution() == "foo.bar"
    assert fake_release(version=expected) == await max_ver.resolve(context)


@pytest.mark.parametrize(
    "versions,expected",
    [
        (["1.0.0", "1.1.0", "1.1.1"], "1.0.0"),
        (["1.1.0", "1.1.1"], "1.1.0"),
        (["1.1.1"], "1.1.1"),
    ],
)
async def test_minimum_ver(versions: Sequence[str], expected: str) -> None:
    context = MagicMock(cr.DistributionContext)
    lazy = cr.minimum_ver(*versions)
    assert Version(expected) == await lazy.resolve(context)


@pytest.mark.parametrize(
    "versions,expected",
    [
        (["1.0.0", "1.1.0", "1.1.1"], "1.1.1"),
        (["1.0.0", "1.1.0"], "1.1.0"),
        (["1.0.0"], "1.0.0"),
    ],
)
async def test_maximum_ver(versions: Sequence[str], expected: str) -> None:
    context = MagicMock(cr.DistributionContext)
    lazy = cr.maximum_ver(*versions)
    assert Version(expected) == await lazy.resolve(context)


@pytest.mark.parametrize(
    "level,version,keep_trailing_zeros,expected",
    [
        (cr.REL_MAJOR, "1.2.3a4dev5", True, "2.0.0"),
        (cr.MICRO, "1.2.3a4dev5", True, "1.2.4"),
        (cr.MINOR, "1.2.3a4dev5", True, "1.3.0"),
        (cr.MAJOR, "1.2.3a4dev5", True, "2.0.0"),
        (cr.REL_MAJOR, "0.1.0", True, "0.2.0"),
        (cr.MICRO, "0.1.0", True, "0.1.1"),
        (cr.MINOR, "0.1.0", True, "0.2.0"),
        (cr.MAJOR, "0.1.0", True, "1.0.0"),
        (cr.REL_MAJOR, "1!1.2.3a4dev5", True, "1!2.0.0"),
        (cr.MICRO, "1!1.2.3a4dev5", True, "1!1.2.4"),
        (cr.MINOR, "1!1.2.3a4dev5", True, "1!1.3.0"),
        (cr.MAJOR, "1!1.2.3a4dev5", True, "1!2.0.0"),
        (cr.REL_MAJOR, "1!0.1.0", True, "1!0.2.0"),
        (cr.MICRO, "1!0.1.0", True, "1!0.1.1"),
        (cr.MINOR, "1!0.1.0", True, "1!0.2.0"),
        (cr.MAJOR, "1!0.1.0", True, "1!1.0.0"),
        (cr.REL_MAJOR, "1.2.3a4dev5", False, "2"),
        (cr.MICRO, "1.2.3a4dev5", False, "1.2.4"),
        (cr.MINOR, "1.2.3a4dev5", False, "1.3"),
        (cr.MAJOR, "1.2.3a4dev5", False, "2"),
        (cr.REL_MAJOR, "0.1.0", False, "0.2"),
        (cr.MICRO, "0.1.0", False, "0.1.1"),
        (cr.MINOR, "0.1.0", False, "0.2"),
        (cr.MAJOR, "0.1.0", False, "1"),
        (cr.REL_MAJOR, "1!1.2.3a4dev5", False, "1!2"),
        (cr.MICRO, "1!1.2.3a4dev5", False, "1!1.2.4"),
        (cr.MINOR, "1!1.2.3a4dev5", False, "1!1.3"),
        (cr.MAJOR, "1!1.2.3a4dev5", False, "1!2"),
        (cr.REL_MAJOR, "1!0.1.0", False, "1!0.2"),
        (cr.MICRO, "1!0.1.0", False, "1!0.1.1"),
        (cr.MINOR, "1!0.1.0", False, "1!0.2"),
        (cr.MAJOR, "1!0.1.0", False, "1!1"),
    ],
)
async def test_ceil_ver(
    level: cr.Level,
    version: str,
    keep_trailing_zeros: bool,
    expected: str,
) -> None:
    context = MagicMock(cr.DistributionContext)
    ceil_ver = cr.ceil_ver(level, version, keep_trailing_zeros)
    assert Version(expected) == await ceil_ver.resolve(context)


@pytest.mark.parametrize(
    "level,version,keep_trailing_zeros,expected",
    [
        (cr.REL_MAJOR, "1.2.3a4dev5", True, "1.0.0"),
        (cr.MICRO, "1.2.3a4dev5", True, "1.2.3"),
        (cr.MINOR, "1.2.3a4dev5", True, "1.2.0"),
        (cr.MAJOR, "1.2.3a4dev5", True, "1.0.0"),
        (cr.REL_MAJOR, "0.1.0", True, "0.1.0"),
        (cr.MICRO, "0.1.0", True, "0.1.0"),
        (cr.MINOR, "0.1.0", True, "0.1.0"),
        (cr.MAJOR, "0.1.0", True, "0.0.0"),
        (cr.REL_MAJOR, "1!1.2.3a4dev5", True, "1!1.0.0"),
        (cr.MICRO, "1!1.2.3a4dev5", True, "1!1.2.3"),
        (cr.MINOR, "1!1.2.3a4dev5", True, "1!1.2.0"),
        (cr.MAJOR, "1!1.2.3a4dev5", True, "1!1.0.0"),
        (cr.REL_MAJOR, "1!0.1.0", True, "1!0.1.0"),
        (cr.MICRO, "1!0.1.0", True, "1!0.1.0"),
        (cr.MINOR, "1!0.1.0", True, "1!0.1.0"),
        (cr.MAJOR, "1!0.1.0", True, "1!0.0.0"),
        (cr.REL_MAJOR, "1.2.3a4dev5", False, "1"),
        (cr.MICRO, "1.2.3a4dev5", False, "1.2.3"),
        (cr.MINOR, "1.2.3a4dev5", False, "1.2"),
        (cr.MAJOR, "1.2.3a4dev5", False, "1"),
        (cr.REL_MAJOR, "0.1.0", False, "0.1"),
        (cr.MICRO, "0.1.0", False, "0.1.0"),
        (cr.MINOR, "0.1.0", False, "0.1"),
        (cr.MAJOR, "0.1.0", False, "0"),
        (cr.REL_MAJOR, "1!1.2.3a4dev5", False, "1!1"),
        (cr.MICRO, "1!1.2.3a4dev5", False, "1!1.2.3"),
        (cr.MINOR, "1!1.2.3a4dev5", False, "1!1.2"),
        (cr.MAJOR, "1!1.2.3a4dev5", False, "1!1"),
        (cr.REL_MAJOR, "1!0.1.0", False, "1!0.1"),
        (cr.MICRO, "1!0.1.0", False, "1!0.1.0"),
        (cr.MINOR, "1!0.1.0", False, "1!0.1"),
        (cr.MAJOR, "1!0.1.0", False, "1!0"),
    ],
)
async def test_floor_ver(
    level: cr.Level,
    version: str,
    keep_trailing_zeros: bool,
    expected: str,
) -> None:
    context = MagicMock(cr.DistributionContext)
    floor_ver = cr.floor_ver(level, version, keep_trailing_zeros)
    assert Version(expected) == await floor_ver.resolve(context)


async def test_min_age() -> None:
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )

    min_age = cr.min_age(
        release_set,
        now=utc(dt.datetime(2023, 8, 16, 16, 5, 0)),
        minutes=3,
        allow_empty=True,
    )
    assert min_age.get_distribution() == "foo.bar"
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
        ],
        infer_successors=False,
    ) == await min_age.resolve(context)


async def test_min_age__context_now() -> None:
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    context.now = utc(dt.datetime(2023, 8, 16, 16, 5, 0))

    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )

    min_age = cr.min_age(release_set, minutes=3, allow_empty=True)
    assert min_age.get_distribution() == "foo.bar"
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
        ],
        infer_successors=False,
    ) == await min_age.resolve(context)


async def test_min_age__empty_allowed() -> None:
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    min_age = cr.min_age(
        release_set,
        now=utc(dt.datetime(2023, 8, 16, 16, 5, 0)),
        minutes=6,
        allow_empty=True,
    )
    assert min_age.get_distribution() == "foo.bar"
    assert fake_release_set(
        releases=[],
        infer_successors=False,
    ) == await min_age.resolve(context)


async def test_min_age__empty_not_allowed() -> None:
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    min_age = cr.min_age(
        release_set,
        now=utc(dt.datetime(2023, 8, 16, 16, 5, 0)),
        minutes=6,
        allow_empty=False,
    )
    assert min_age.get_distribution() == "foo.bar"
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
        ],
        infer_successors=False,
    ) == await min_age.resolve(context)


async def test_max_age() -> None:
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    max_age = cr.max_age(
        release_set,
        now=utc(dt.datetime(2023, 8, 16, 16, 5, 0)),
        minutes=3,
        allow_empty=True,
    )
    assert max_age.get_distribution() == "foo.bar"
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    ) == await max_age.resolve(context)


async def test_max_age__context_now() -> None:
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    context.now = utc(dt.datetime(2023, 8, 16, 16, 5, 0))
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    max_age = cr.max_age(release_set, minutes=3, allow_empty=True)
    assert max_age.get_distribution() == "foo.bar"
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    ) == await max_age.resolve(context)


async def test_max_age__empty_allowed() -> None:
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    max_age = cr.max_age(
        release_set,
        now=utc(dt.datetime(2023, 8, 16, 16, 10, 0)),
        minutes=3,
        allow_empty=True,
    )
    assert max_age.get_distribution() == "foo.bar"
    assert fake_release_set(
        releases=[],
        infer_successors=False,
    ) == await max_age.resolve(context)


async def test_max_age__empty_not_allowed() -> None:
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    max_age = cr.max_age(
        release_set,
        now=utc(dt.datetime(2023, 8, 16, 16, 10, 0)),
        minutes=3,
        allow_empty=False,
    )
    assert max_age.get_distribution() == "foo.bar"
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    ) == await max_age.resolve(context)


@pytest.mark.parametrize(
    "level,n,releases,expected",
    [
        (
            cr.MAJOR,
            3,
            [
                "1.0.0",
                "2.0.0",
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
            [
                "1.0.0",
                "2.0.0",
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
        ),
        (
            cr.MINOR,
            3,
            [
                "1.0.0",
                "2.0.0",
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
            [
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
        ),
        (
            cr.MICRO,
            3,
            [
                "1.0.0",
                "2.0.0",
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
            [
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
        ),
        (
            cr.MINOR,
            3,
            [
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
            [
                "2.2.0",
                "1!1.0.0",
            ],
        ),
    ],
)
async def test_count(
    level: cr.Level,
    n: int,
    releases: Collection[str],
    expected: Collection[str],
) -> None:
    release_set = fake_release_set(releases=releases, infer_successors=False)
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    count = cr.count(level, n, release_set)

    assert count.get_distribution() == "foo.bar"
    assert fake_release_set(releases=expected, infer_successors=False) == await count.resolve(
        context,
    )


async def test_requirements(monkeypatch: MonkeyPatch) -> None:
    context = MagicMock(cr.Context)
    context.default_python = Version("3.9")
    dcontext = MagicMock(cr.DistributionContext)
    dcontext.distribution = "foo.bar"
    context.for_distribution.return_value = dcontext
    release = fake_release(version="1.2.3")

    requirements = cr.get_requirement_set([Requirement("foo>=1.0.0"), Requirement("bar>=2.0.0")])
    metadata = MagicMock(cr.DistributionMetadata)
    metadata.requires = requirements

    venv = MagicMock(cr.VirtualEnv)
    venv.distribution_metadata.return_value = metadata

    @asynccontextmanager
    async def fake_venv(python_version: Version) -> AsyncIterator[cr.VirtualEnv]:
        assert context.default_python == python_version
        yield venv

    monkeypatch.setattr("compreq.operators.temp_venv", fake_venv)

    lazy = cr.requirements(release)

    assert requirements == await lazy.resolve(context)
    context.for_distribution.assert_called_once_with("foo.bar")
    venv.install.assert_called_once_with(
        cr.get_requirement_set([Requirement("foo.bar==1.2.3")]),
        deps=False,
    )
    venv.distribution_metadata.assert_called_once_with("foo.bar")


async def test_consistent_lower_bounds(monkeypatch: MonkeyPatch) -> None:
    context = MagicMock(cr.Context)

    requirement_set = cr.get_requirement_set(
        [
            Requirement("python<4.0,>=3.9"),
            Requirement("dist1<2.0.0,>=1.2.3; python_version >= '3.10'"),
            Requirement("dist2[extra]>=2.0.0,!=2.1.1"),
            Requirement("dist3>1.0.0"),
            Requirement("dist4"),
        ],
    )

    def fake_distribution_metadata(distribution: str) -> cr.DistributionMetadata:
        metadata = MagicMock(cr.DistributionMetadata)
        metadata.version = Version(
            {
                "dist1": "1.2.0",
                "dist2": "1.12.0",
            }[distribution],
        )
        return metadata

    venv = MagicMock(cr.VirtualEnv)
    venv.distribution_metadata.side_effect = fake_distribution_metadata

    @asynccontextmanager
    async def fake_venv(python_version: Version) -> AsyncIterator[cr.VirtualEnv]:
        assert Version("3.9") == python_version
        yield venv

    monkeypatch.setattr("compreq.operators.temp_venv", fake_venv)

    lazy = cr.consistent_lower_bounds(requirement_set)

    assert cr.get_requirement_set(
        [
            Requirement("python<4.0,>=3.9"),
            Requirement("dist1<2.0.0,>=1.2.0; python_version >= '3.10'"),
            Requirement("dist2[extra]>=1.12.0,!=2.1.1"),
            Requirement("dist3>1.0.0"),
            Requirement("dist4"),
        ],
    ) == await lazy.resolve(context)
    venv.install.assert_called_once_with(
        cr.get_requirement_set(
            [
                Requirement("dist1<=1.2.3"),
                Requirement("dist2[extra]<=2.0.0,!=2.1.1"),
                Requirement("dist3>1.0.0"),
                Requirement("dist4"),
            ],
        ),
    )


async def test_consistent_lower_bounds__no_python(monkeypatch: MonkeyPatch) -> None:
    context = MagicMock(cr.Context)
    context.default_python = Version("3.9")

    requirement_set = cr.get_requirement_set(
        [
            Requirement("dist1<2.0.0,>=1.2.3; python_version >= '3.10'"),
            Requirement("dist2[extra]>=2.0.0,!=2.1.1"),
            Requirement("dist3>1.0.0"),
            Requirement("dist4"),
        ],
    )

    def fake_distribution_metadata(distribution: str) -> cr.DistributionMetadata:
        metadata = MagicMock(cr.DistributionMetadata)
        metadata.version = Version(
            {
                "dist1": "1.2.0",
                "dist2": "1.12.0",
            }[distribution],
        )
        return metadata

    venv = MagicMock(cr.VirtualEnv)
    venv.distribution_metadata.side_effect = fake_distribution_metadata

    @asynccontextmanager
    async def fake_venv(python_version: Version) -> AsyncIterator[cr.VirtualEnv]:
        assert context.default_python == python_version
        yield venv

    monkeypatch.setattr("compreq.operators.temp_venv", fake_venv)

    lazy = cr.consistent_lower_bounds(requirement_set)

    assert cr.get_requirement_set(
        [
            Requirement("dist1<2.0.0,>=1.2.0; python_version >= '3.10'"),
            Requirement("dist2[extra]>=1.12.0,!=2.1.1"),
            Requirement("dist3>1.0.0"),
            Requirement("dist4"),
        ],
    ) == await lazy.resolve(context)
    venv.install.assert_called_once_with(
        cr.get_requirement_set(
            [
                Requirement("dist1<=1.2.3"),
                Requirement("dist2[extra]<=2.0.0,!=2.1.1"),
                Requirement("dist3>1.0.0"),
                Requirement("dist4"),
            ],
        ),
    )
