from unittest.mock import MagicMock

import pytest
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

import compreq as cr
from tests.utils import fake_release, fake_release_set


async def test_eager_lazy_release() -> None:
    release = fake_release()
    lazy = cr.EagerLazyRelease(release)

    context = MagicMock(cr.DistributionContext)
    assert lazy.get_distribution() == "foo.bar"
    assert release == await lazy.resolve(context)


@pytest.mark.parametrize(
    "release,expected",
    [
        (
            fake_release(version="1.1.0"),
            cr.EagerLazyRelease(fake_release(version="1.1.0")),
        ),
        (
            cr.EagerLazyRelease(fake_release(version="1.2.0")),
            cr.EagerLazyRelease(fake_release(version="1.2.0")),
        ),
    ],
)
def test_get_lazy_release(release: cr.AnyRelease, expected: cr.LazyRelease) -> None:
    assert expected == cr.get_lazy_release(release)


async def test_eager_lazy_release_set__empty() -> None:
    lazy = cr.EagerLazyReleaseSet(frozenset())
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"

    assert lazy.get_distribution() is None
    assert cr.ReleaseSet("foo.bar", frozenset()) == await lazy.resolve(context)


async def test_eager_lazy_release_set() -> None:
    release_2 = fake_release(version="1.2.0")
    release_1 = fake_release(version="1.1.0", successor=release_2)

    lazy = cr.EagerLazyReleaseSet(
        frozenset([cr.get_lazy_release(release_1), cr.get_lazy_release(release_2)]),
    )
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"

    assert lazy.get_distribution() == "foo.bar"
    assert cr.ReleaseSet("foo.bar", frozenset([release_1, release_2])) == await lazy.resolve(
        context,
    )


async def test_all_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"],
    )

    lazy = cr.AllLazyReleaseSet(None)
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    context.releases.return_value = releases

    assert lazy.get_distribution() is None
    assert fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"],
    ) == await lazy.resolve(context)
    context.releases.assert_called_once_with("foo.bar")


async def test_all_lazy_release_set__distribution() -> None:
    releases = fake_release_set(
        distribution="foo",
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"],
    )

    lazy = cr.AllLazyReleaseSet("foo")
    context = MagicMock(cr.DistributionContext)
    context.distribution = "foo.bar"
    context.releases.return_value = releases

    assert lazy.get_distribution() == "foo"
    assert (
        releases
        == fake_release_set(
            distribution="foo",
            releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"],
        )
        == await lazy.resolve(context)
    )
    context.releases.assert_called_once_with("foo")


async def test_prod_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"],
    )
    source = MagicMock(cr.LazyReleaseSet)
    source.get_distribution.return_value = "foo"
    source.resolve.return_value = releases
    context = MagicMock(cr.DistributionContext)

    lazy = cr.ProdLazyReleaseSet(source)

    assert lazy.get_distribution() == "foo"
    assert fake_release_set(releases=["1.2.0", "1.3.0"]) == await lazy.resolve(context)
    source.resolve.assert_called_once_with(context)


async def test_pre_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"],
    )
    source = MagicMock(cr.LazyReleaseSet)
    source.get_distribution.return_value = "foo"
    source.resolve.return_value = releases
    context = MagicMock(cr.DistributionContext)

    lazy = cr.PreLazyReleaseSet(source)

    assert lazy.get_distribution() == "foo"
    assert fake_release_set(releases=["1.2.0", "1.3.0.rc1", "1.3.0"]) == await lazy.resolve(context)
    source.resolve.assert_called_once_with(context)


async def test_specifier_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.2.1", "1.3.0", "1.3.1", "1.4.0", "2.0.0", "2.1.0"],
        infer_successors=False,
    )
    source = MagicMock(cr.LazyReleaseSet)
    source.get_distribution.return_value = "foo"
    source.resolve.return_value = releases
    context = MagicMock(cr.DistributionContext)

    lazy = cr.SpecifierLazyReleaseSet(source, cr.get_lazy_specifier_set(">=1.3.0,<2.0.0"))

    assert lazy.get_distribution() == "foo"
    assert fake_release_set(
        releases=["1.3.0", "1.3.1", "1.4.0"],
        infer_successors=False,
    ) == await lazy.resolve(context)
    source.resolve.assert_called_once_with(context)


@pytest.mark.parametrize(
    "release_set,expected",
    [
        (
            None,
            cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet(None)),
        ),
        (
            "foo.bar",
            cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet("foo.bar")),
        ),
        (
            fake_release(version="1.1.0"),
            cr.EagerLazyReleaseSet(frozenset([cr.EagerLazyRelease(fake_release(version="1.1.0"))])),
        ),
        (
            cr.EagerLazyRelease(fake_release(version="1.2.0")),
            cr.EagerLazyReleaseSet(frozenset([cr.EagerLazyRelease(fake_release(version="1.2.0"))])),
        ),
        (
            cr.ReleaseSet("foo.bar", frozenset()),
            cr.EagerLazyReleaseSet(frozenset()),
        ),
        (
            cr.ReleaseSet(
                "foo.bar",
                frozenset(
                    [
                        fake_release(version="1.3.0"),
                        fake_release(version="1.4.0"),
                    ],
                ),
            ),
            cr.EagerLazyReleaseSet(
                frozenset(
                    [
                        cr.EagerLazyRelease(fake_release(version="1.3.0")),
                        cr.EagerLazyRelease(fake_release(version="1.4.0")),
                    ],
                ),
            ),
        ),
        (
            cr.EagerLazyReleaseSet(frozenset()),
            cr.EagerLazyReleaseSet(frozenset()),
        ),
        (
            cr.EagerLazyReleaseSet(
                frozenset(
                    [
                        cr.EagerLazyRelease(fake_release(version="1.5.0")),
                        cr.EagerLazyRelease(fake_release(version="1.6.0")),
                    ],
                ),
            ),
            cr.EagerLazyReleaseSet(
                frozenset(
                    [
                        cr.EagerLazyRelease(fake_release(version="1.5.0")),
                        cr.EagerLazyRelease(fake_release(version="1.6.0")),
                    ],
                ),
            ),
        ),
        (
            Specifier("==1.7.0"),
            cr.SpecifierLazyReleaseSet(
                cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet(None)),
                cr.get_lazy_specifier_set("==1.7.0"),
            ),
        ),
        (
            cr.get_lazy_specifier("==1.8.0"),
            cr.SpecifierLazyReleaseSet(
                cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet(None)),
                cr.get_lazy_specifier_set("==1.8.0"),
            ),
        ),
        (
            SpecifierSet(">=1.9.1,<2.0.0"),
            cr.SpecifierLazyReleaseSet(
                cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet(None)),
                cr.get_lazy_specifier_set(">=1.9.1,<2.0.0"),
            ),
        ),
        (
            cr.get_lazy_specifier_set(">=1.10.2,<2.0.0"),
            cr.SpecifierLazyReleaseSet(
                cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet(None)),
                cr.get_lazy_specifier_set(">=1.10.2,<2.0.0"),
            ),
        ),
        (
            Requirement("foo.bar>=1.11.1,<2.0.0"),
            cr.SpecifierLazyReleaseSet(
                cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet("foo.bar")),
                cr.get_lazy_specifier_set(">=1.11.1,<2.0.0"),
            ),
        ),
        (
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">=1.12.3,<2.0.0"),
                marker=None,
                optional=True,
            ),
            cr.SpecifierLazyReleaseSet(
                cr.ProdLazyReleaseSet(cr.AllLazyReleaseSet("foo.bar")),
                cr.get_lazy_specifier_set(">=1.12.3,<2.0.0"),
            ),
        ),
    ],
)
def test_get_lazy_release_set(release_set: cr.AnyReleaseSet, expected: cr.LazyReleaseSet) -> None:
    assert expected == cr.get_lazy_release_set(release_set)


async def test_eager_lazy_version() -> None:
    version = Version("1.1.0")
    lazy = cr.EagerLazyVersion(version)

    context = MagicMock(cr.DistributionContext)
    assert version == await lazy.resolve(context)


async def test_release_lazy_version() -> None:
    version = Version("3.1.2")
    release = cr.EagerLazyRelease(fake_release(version=version))
    lazy = cr.ReleaseLazyVersion(release)

    context = MagicMock(cr.DistributionContext)
    assert version == await lazy.resolve(context)


@pytest.mark.parametrize(
    "version,expected",
    [
        ("1.0.0", cr.EagerLazyVersion(Version("1.0.0"))),
        (
            fake_release(version="1.1.0"),
            cr.EagerLazyVersion(Version("1.1.0")),
        ),
        (
            cr.EagerLazyRelease(
                fake_release(version="1.2.0"),
            ),
            cr.ReleaseLazyVersion(
                cr.EagerLazyRelease(
                    fake_release(version="1.2.0"),
                ),
            ),
        ),
        (Version("1.3.0"), cr.EagerLazyVersion(Version("1.3.0"))),
        (cr.EagerLazyVersion(Version("1.4.0")), cr.EagerLazyVersion(Version("1.4.0"))),
    ],
)
def test_get_lazy_version(version: cr.AnyVersion, expected: cr.LazyVersion) -> None:
    assert expected == cr.get_lazy_version(version)


@pytest.mark.parametrize(
    "op,expected",
    [
        ("~=", cr.SpecifierOperator.COMPATIBLE),
        (cr.SpecifierOperator.NE, cr.SpecifierOperator.NE),
    ],
)
def test_get_specifier_operator(
    op: cr.AnySpecifierOperator,
    expected: cr.SpecifierOperator,
) -> None:
    assert cr.get_specifier_operator(op) == expected


async def test_eager_lazy_specifier() -> None:
    op = cr.SpecifierOperator.LT
    version = MagicMock(cr.LazyVersion)
    version.resolve.return_value = Version("1.5.0")
    lazy = cr.EagerLazySpecifier(op, version)

    context = MagicMock(cr.DistributionContext)
    assert Specifier("<1.5.0") == await lazy.resolve(context)
    version.resolve.assert_called_once_with(context)


async def test_release_lazy_specifier() -> None:
    release = MagicMock(cr.LazyRelease)
    release.resolve.return_value = fake_release(version="1.7.8")
    lazy = cr.ReleaseLazySpecifier(release)

    context = MagicMock(cr.DistributionContext)
    assert Specifier("==1.7.8") == await lazy.resolve(context)
    release.resolve.assert_called_once_with(context)


@pytest.mark.parametrize(
    "specifier,expected",
    [
        (
            ">=1.1.0",
            cr.EagerLazySpecifier(cr.SpecifierOperator.GE, cr.EagerLazyVersion(Version("1.1.0"))),
        ),
        (
            fake_release(version="2.1.4"),
            cr.ReleaseLazySpecifier(cr.EagerLazyRelease(fake_release(version="2.1.4"))),
        ),
        (
            cr.EagerLazyRelease(fake_release(version="2.1.4")),
            cr.ReleaseLazySpecifier(cr.EagerLazyRelease(fake_release(version="2.1.4"))),
        ),
        (
            Specifier(">=1.2.0"),
            cr.EagerLazySpecifier(cr.SpecifierOperator.GE, cr.EagerLazyVersion(Version("1.2.0"))),
        ),
        (
            cr.EagerLazySpecifier(cr.SpecifierOperator.GE, cr.EagerLazyVersion(Version("1.3.0"))),
            cr.EagerLazySpecifier(cr.SpecifierOperator.GE, cr.EagerLazyVersion(Version("1.3.0"))),
        ),
    ],
)
def test_get_lazy_specifier(specifier: cr.AnySpecifier, expected: cr.LazySpecifier) -> None:
    assert cr.get_lazy_specifier(specifier) == expected


async def test_eager_lazy_specifier_set() -> None:
    specifier_1 = MagicMock(cr.LazySpecifier)
    specifier_1.resolve.return_value = Specifier(">=1.2.3")
    specifier_2 = MagicMock(cr.LazySpecifier)
    specifier_2.resolve.return_value = Specifier("<2.0.0")

    lazy = cr.EagerLazySpecifierSet(frozenset([specifier_1, specifier_2]))

    context = MagicMock(cr.DistributionContext)
    assert SpecifierSet(">=1.2.3,<2.0.0") == await lazy.resolve(context)
    specifier_1.resolve.assert_called_once_with(context)
    specifier_2.resolve.assert_called_once_with(context)


async def test_composite_lazy_specifier_set() -> None:
    specifier_1 = MagicMock(cr.LazySpecifierSet)
    specifier_1.resolve.return_value = SpecifierSet("<2.0.0,>=1.2.3")
    specifier_2 = MagicMock(cr.LazySpecifierSet)
    specifier_2.resolve.return_value = SpecifierSet("!=1.2.4,!=1.2.5")

    lazy = cr.CompositeLazySpecifierSet(frozenset([specifier_1, specifier_2]))

    context = MagicMock(cr.DistributionContext)
    assert SpecifierSet(">=1.2.3,<2.0.0,!=1.2.4,!=1.2.5") == await lazy.resolve(context)
    specifier_1.resolve.assert_called_once_with(context)
    specifier_2.resolve.assert_called_once_with(context)


@pytest.mark.parametrize(
    "specifier_set,expected",
    [
        (">=1.1.0", cr.EagerLazySpecifierSet(frozenset([cr.get_lazy_specifier(">=1.1.0")]))),
        (
            fake_release(version="2.1.4"),
            cr.EagerLazySpecifierSet(
                frozenset(
                    [cr.ReleaseLazySpecifier(cr.EagerLazyRelease(fake_release(version="2.1.4")))],
                ),
            ),
        ),
        (
            cr.EagerLazyRelease(fake_release(version="2.1.4")),
            cr.EagerLazySpecifierSet(
                frozenset(
                    [cr.ReleaseLazySpecifier(cr.EagerLazyRelease(fake_release(version="2.1.4")))],
                ),
            ),
        ),
        (
            Specifier(">=1.2.0"),
            cr.EagerLazySpecifierSet(frozenset([cr.get_lazy_specifier(">=1.2.0")])),
        ),
        (
            cr.get_lazy_specifier(">=1.3.0"),
            cr.EagerLazySpecifierSet(frozenset([cr.get_lazy_specifier(">=1.3.0")])),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            cr.EagerLazySpecifierSet(
                frozenset([cr.get_lazy_specifier(">=1.4.0"), cr.get_lazy_specifier("<2.0.0")]),
            ),
        ),
        (
            cr.EagerLazySpecifierSet(
                frozenset([cr.get_lazy_specifier(">=1.5.0"), cr.get_lazy_specifier("<2.0.0")]),
            ),
            cr.EagerLazySpecifierSet(
                frozenset([cr.get_lazy_specifier(">=1.5.0"), cr.get_lazy_specifier("<2.0.0")]),
            ),
        ),
    ],
)
def test_get_lazy_specifier_set(
    specifier_set: cr.AnySpecifierSet,
    expected: cr.LazySpecifierSet,
) -> None:
    assert cr.get_lazy_specifier_set(specifier_set) == expected


@pytest.mark.parametrize(
    "marker,expected",
    [
        ("python_version > '1.0'", Marker("python_version > '1.0'")),
        (Marker("python_version > '1.1'"), Marker("python_version > '1.1'")),
    ],
)
def test_get_marker(marker: cr.AnyMarker, expected: Marker) -> None:
    assert expected == cr.get_marker(marker)


async def test_lazy_requirement__specifier() -> None:
    specifier_set = MagicMock(cr.LazySpecifierSet)
    specifier_set.resolve.return_value = SpecifierSet(">=1.2.3,<2.0.0")
    requirement = cr.LazyRequirement(
        "foo.bar",
        None,
        frozenset(["extra_1", "extra_2"]),
        specifier_set,
        Marker("python_version>'2.0'"),
        optional=True,
    )

    distribution_context = MagicMock(cr.DistributionContext)
    context = MagicMock(cr.Context)
    context.for_distribution.return_value = distribution_context

    assert cr.OptionalRequirement(
        Requirement("foo.bar[extra_1,extra_2]<2.0.0,>=1.2.3; python_version > '2.0'"),
        True,
    ) == await requirement.resolve(context)
    context.for_distribution.assert_called_once_with("foo.bar")
    specifier_set.resolve.assert_called_once_with(distribution_context)


async def test_lazy_requirement__url() -> None:
    requirement = cr.LazyRequirement(
        "foo.bar",
        "http://path1/path2",
        frozenset(),
        None,
        None,
        optional=None,
    )

    distribution_context = MagicMock(cr.DistributionContext)
    context = MagicMock(cr.Context)
    context.for_distribution.return_value = distribution_context

    assert cr.OptionalRequirement(
        Requirement("foo.bar@ http://path1/path2"),
        False,
    ) == await requirement.resolve(context)
    context.for_distribution.assert_called_once_with("foo.bar")


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            "foo.bar",
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
            "foo.bar==1.1.0",
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set("==1.1.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            fake_release(version="1.2.3"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(fake_release(version="1.2.3")),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.EagerLazyRelease(fake_release(version="1.2.3")),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(fake_release(version="1.2.3")),
                marker=None,
                optional=None,
            ),
        ),
        (
            Specifier("==1.2.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set("==1.2.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.get_lazy_specifier("==1.3.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set("==1.3.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.get_lazy_specifier_set(">=1.4.0,<2.0.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.OptionalRequirement(
                Requirement("foo.bar[extra]==1.5.0; python_version > '2.0.0'"),
                True,
            ),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=cr.get_lazy_specifier_set("==1.5.0"),
                marker=Marker("python_version > '2.0.0'"),
                optional=True,
            ),
        ),
        (
            cr.OptionalRequirement(Requirement("foo.bar@http://path/v1.6.0"), False),
            cr.LazyRequirement(
                distribution="foo.bar",
                url="http://path/v1.6.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=False,
            ),
        ),
        (
            Requirement("foo.bar[extra]==1.5.0; python_version > '2.0.0'"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=cr.get_lazy_specifier_set("==1.5.0"),
                marker=Marker("python_version > '2.0.0'"),
                optional=None,
            ),
        ),
        (
            Requirement("foo.bar@http://path/v1.6.0"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url="http://path/v1.6.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=cr.get_lazy_specifier_set("==1.7.0"),
                marker=Marker("python_version > '2.0.0'"),
                optional=True,
            ),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=cr.get_lazy_specifier_set("==1.7.0"),
                marker=Marker("python_version > '2.0.0'"),
                optional=True,
            ),
        ),
        (
            cr.LazyRequirement(
                distribution="foo.bar",
                url="http://path/v1.8.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=False,
            ),
            cr.LazyRequirement(
                distribution="foo.bar",
                url="http://path/v1.8.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=False,
            ),
        ),
    ],
)
def test_get_lazy_requirement(requirement: cr.AnyRequirement, expected: cr.LazyRequirement) -> None:
    assert cr.get_lazy_requirement(requirement) == expected


@pytest.mark.parametrize(
    "lhs,rhs,expected",
    [
        # Distribution
        (
            cr.distribution("foo.bar"),
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
            cr.distribution("foo.bar"),
            cr.distribution("foo"),
            AssertionError,
        ),
        (
            cr.distribution("foo.bar"),
            cr.url("http://path/v1.3.0"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url="http://path/v1.3.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.distribution("foo.bar"),
            cr.extra("extra1"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(["extra1"]),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.distribution("foo.bar"),
            cr.specifier(">1.5.0"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">1.5.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.distribution("foo.bar"),
            cr.specifier_set(">1.5.0"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">1.5.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.distribution("foo.bar"),
            cr.marker("python_version>'2.1'"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version>'2.1'"),
                optional=None,
            ),
        ),
        (
            cr.distribution("foo.bar"),
            cr.optional(),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=True,
            ),
        ),
        # Url
        (
            cr.url("http://path/v2.0.0"),
            cr.distribution("foo.bar"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url="http://path/v2.0.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.url("http://path/v2.0.0"),
            cr.LazyRequirement(
                distribution=None,
                url="http://path/v2.0.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.extra("extra1"),
            cr.LazyRequirement(
                distribution=None,
                url="http://path/v2.0.0",
                extras=frozenset(["extra1"]),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.specifier(">1.5.0"),
            AssertionError,
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.specifier_set(">1.5.0"),
            AssertionError,
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.marker("python_version>'2.1'"),
            cr.LazyRequirement(
                distribution=None,
                url="http://path/v2.0.0",
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version>'2.1'"),
                optional=None,
            ),
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.optional(),
            cr.LazyRequirement(
                distribution=None,
                url="http://path/v2.0.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=True,
            ),
        ),
        # Extra
        (
            cr.extra("extra"),
            cr.distribution("foo.bar"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.url("http://path/v1.3.0"),
            cr.LazyRequirement(
                distribution=None,
                url="http://path/v1.3.0",
                extras=frozenset(["extra"]),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.extra("extra"),
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
            cr.extra("extra"),
            cr.extra("extra1"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra", "extra1"]),
                specifier=None,
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.specifier(">1.5.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=cr.get_lazy_specifier_set(">1.5.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.specifier_set(">1.5.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=cr.get_lazy_specifier_set(">1.5.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.marker("python_version>'2.1'"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=None,
                marker=Marker("python_version>'2.1'"),
                optional=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.optional(),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=None,
                marker=None,
                optional=True,
            ),
        ),
        # Specifier
        (
            cr.specifier("==2.0.0"),
            cr.distribution("foo.bar"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=cr.EagerLazySpecifierSet(frozenset([cr.get_lazy_specifier("==2.0.0")])),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            cr.specifier("==2.0.0"),
            cr.extra("extra1"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra1"]),
                specifier=cr.get_lazy_specifier_set("==2.0.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.specifier("==2.0.0"),
            cr.get_lazy_specifier_set("==2.0.0"),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.specifier(">1.5.0"),
            cr.get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.specifier_set(">1.5.0"),
            cr.get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.marker("python_version>'2.1'"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set("==2.0.0"),
                marker=Marker("python_version>'2.1'"),
                optional=None,
            ),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.optional(),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set("==2.0.0"),
                marker=None,
                optional=True,
            ),
        ),
        # Specifier set
        (
            cr.specifier_set("==2.0.0"),
            cr.distribution("foo.bar"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=cr.EagerLazySpecifierSet(frozenset([cr.get_lazy_specifier("==2.0.0")])),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.extra("extra1"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra1"]),
                specifier=cr.get_lazy_specifier_set("==2.0.0"),
                marker=None,
                optional=None,
            ),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.specifier(">1.5.0"),
            cr.get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.specifier_set("==2.0.0"),
            cr.get_lazy_specifier_set("==2.0.0"),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.specifier_set(">1.5.0"),
            cr.get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.marker("python_version>'2.1'"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set("==2.0.0"),
                marker=Marker("python_version>'2.1'"),
                optional=None,
            ),
        ),
        (
            cr.optional(),
            cr.marker("python_version>'2.1'"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version>'2.1'"),
                optional=True,
            ),
        ),
        # Marker
        (
            cr.marker("python_version=='3.0'"),
            cr.distribution("foo.bar"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version=='3.0'"),
                optional=None,
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.url("http://path/v1.3.0"),
            cr.LazyRequirement(
                distribution=None,
                url="http://path/v1.3.0",
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version=='3.0'"),
                optional=None,
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.extra("extra1"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra1"]),
                specifier=None,
                marker=Marker("python_version=='3.0'"),
                optional=None,
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.specifier(">1.5.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">1.5.0"),
                marker=Marker("python_version=='3.0'"),
                optional=None,
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.specifier_set(">1.5.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">1.5.0"),
                marker=Marker("python_version=='3.0'"),
                optional=None,
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.marker("python_version=='3.0'"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version=='3.0'"),
                optional=None,
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.marker("python_version>'2.1'"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version=='3.0' and python_version>'2.1'"),
                optional=None,
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.optional(),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version=='3.0'"),
                optional=True,
            ),
        ),
        # Optional
        (
            cr.optional(),
            cr.distribution("foo.bar"),
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=True,
            ),
        ),
        (
            cr.optional(),
            cr.url("http://path/v1.3.0"),
            cr.LazyRequirement(
                distribution=None,
                url="http://path/v1.3.0",
                extras=frozenset(),
                specifier=None,
                marker=None,
                optional=True,
            ),
        ),
        (
            cr.optional(),
            cr.extra("extra1"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(["extra1"]),
                specifier=None,
                marker=None,
                optional=True,
            ),
        ),
        (
            cr.optional(),
            cr.specifier(">1.5.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">1.5.0"),
                marker=None,
                optional=True,
            ),
        ),
        (
            cr.optional(),
            cr.specifier_set(">1.5.0"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=cr.get_lazy_specifier_set(">1.5.0"),
                marker=None,
                optional=True,
            ),
        ),
        (
            cr.optional(),
            cr.marker("python_version=='3.0'"),
            cr.LazyRequirement(
                distribution=None,
                url=None,
                extras=frozenset(),
                specifier=None,
                marker=Marker("python_version=='3.0'"),
                optional=True,
            ),
        ),
        (
            cr.optional(),
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
        (
            cr.optional(),
            cr.optional(False),
            AssertionError,
        ),
    ],
)
def test_compose(
    lhs: cr.LazyRequirement,
    rhs: cr.LazyRequirement,
    expected: cr.LazyRequirement | cr.LazySpecifierSet | type[Exception],
) -> None:
    if isinstance(expected, type):
        with pytest.raises(expected):
            lhs & rhs
    else:
        assert (lhs & rhs) == expected


def test_compose__specifier_sets() -> None:
    specifier_1 = MagicMock(cr.LazySpecifier)
    specifier_2 = MagicMock(cr.LazySpecifier)
    specifier_3 = MagicMock(cr.LazySpecifier)
    specifier_set_1 = MagicMock(cr.LazySpecifierSet)
    specifier_set_2 = MagicMock(cr.LazySpecifierSet)
    specifier_set_3 = MagicMock(cr.LazySpecifierSet)

    eager_1 = cr.EagerLazySpecifierSet(frozenset([specifier_1, specifier_2]))
    eager_2 = cr.EagerLazySpecifierSet(frozenset([specifier_1, specifier_3]))
    composite_1 = cr.CompositeLazySpecifierSet(frozenset([specifier_set_1, specifier_set_2]))
    composite_2 = cr.CompositeLazySpecifierSet(frozenset([specifier_set_1, specifier_set_3]))

    assert cr.EagerLazySpecifierSet(
        frozenset([specifier_1, specifier_2, specifier_3]),
    ) == cr.compose(eager_1, eager_2)
    assert cr.CompositeLazySpecifierSet(
        frozenset([eager_1, specifier_set_1, specifier_set_2]),
    ) == cr.compose(eager_1, composite_1)
    assert cr.CompositeLazySpecifierSet(
        frozenset([eager_1, specifier_set_1, specifier_set_2]),
    ) == cr.compose(composite_1, eager_1)
    assert cr.CompositeLazySpecifierSet(
        frozenset([specifier_set_1, specifier_set_2, specifier_set_3]),
    ) == cr.compose(composite_1, composite_2)


@pytest.mark.parametrize(
    "requirement_set,expected",
    [
        (
            "foo.bar",
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo.bar",
                            url=None,
                            extras=frozenset(),
                            specifier=None,
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            "foo.bar==1.1.0",
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo.bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==1.1.0"),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            fake_release(version="1.2.3"),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo.bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(fake_release(version="1.2.3")),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            cr.EagerLazyRelease(fake_release(version="1.2.3")),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo.bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(fake_release(version="1.2.3")),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            Specifier("==1.2.0"),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution=None,
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==1.2.0"),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            cr.get_lazy_specifier("==1.3.0"),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution=None,
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==1.3.0"),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution=None,
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            cr.get_lazy_specifier_set(">=1.4.0,<2.0.0"),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution=None,
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            cr.OptionalRequirement(
                Requirement("foo.bar[extra]==1.5.0; python_version > '2.0.0'"),
                True,
            ),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo.bar",
                            url=None,
                            extras=frozenset(["extra"]),
                            specifier=cr.get_lazy_specifier_set("==1.5.0"),
                            marker=Marker("python_version > '2.0.0'"),
                            optional=True,
                        ),
                    ],
                ),
            ),
        ),
        (
            Requirement("foo.bar[extra]==1.5.0; python_version > '2.0.0'"),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo.bar",
                            url=None,
                            extras=frozenset(["extra"]),
                            specifier=cr.get_lazy_specifier_set("==1.5.0"),
                            marker=Marker("python_version > '2.0.0'"),
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            cr.LazyRequirement(
                distribution="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=cr.get_lazy_specifier_set("==1.7.0"),
                marker=Marker("python_version > '2.0.0'"),
                optional=True,
            ),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo.bar",
                            url=None,
                            extras=frozenset(["extra"]),
                            specifier=cr.get_lazy_specifier_set("==1.7.0"),
                            marker=Marker("python_version > '2.0.0'"),
                            optional=True,
                        ),
                    ],
                ),
            ),
        ),
        (
            [
                cr.OptionalRequirement(Requirement("foo>=1.2.3"), True),
                cr.OptionalRequirement(Requirement("bar==2.0.0"), False),
            ],
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                            optional=True,
                        ),
                        cr.LazyRequirement(
                            distribution="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                            optional=False,
                        ),
                    ],
                ),
            ),
        ),
        (
            [
                Requirement("foo>=1.2.3"),
                Requirement("bar==2.0.0"),
            ],
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                            optional=None,
                        ),
                        cr.LazyRequirement(
                            distribution="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            {
                "foo": cr.OptionalRequirement(Requirement("foo>=1.2.3"), True),
                "bar": cr.OptionalRequirement(Requirement("bar==2.0.0"), False),
            },
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                            optional=True,
                        ),
                        cr.LazyRequirement(
                            distribution="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                            optional=False,
                        ),
                    ],
                ),
            ),
        ),
        (
            {
                "foo": Requirement("foo>=1.2.3"),
                "bar": Requirement("bar==2.0.0"),
            },
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                            optional=None,
                        ),
                        cr.LazyRequirement(
                            distribution="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                            optional=None,
                        ),
                    ],
                ),
            ),
        ),
        (
            cr.get_requirement_set(
                [
                    Requirement("foo>=1.2.3"),
                    Requirement("bar==2.0.0"),
                ],
            ),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                            optional=False,
                        ),
                        cr.LazyRequirement(
                            distribution="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                            optional=False,
                        ),
                    ],
                ),
            ),
        ),
        (
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                            optional=True,
                        ),
                        cr.LazyRequirement(
                            distribution="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                            optional=False,
                        ),
                    ],
                ),
            ),
            cr.EagerLazyRequirementSet(
                frozenset(
                    [
                        cr.LazyRequirement(
                            distribution="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                            optional=True,
                        ),
                        cr.LazyRequirement(
                            distribution="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=cr.get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                            optional=False,
                        ),
                    ],
                ),
            ),
        ),
    ],
)
def test_get_lazy_requirement_set(
    requirement_set: cr.AnyRequirementSet,
    expected: cr.LazyRequirementSet,
) -> None:
    assert cr.get_lazy_requirement_set(requirement_set) == expected
