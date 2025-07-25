from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from itertools import chain
from typing import Final, TypeAlias, Union, overload

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from compreq.contexts import Context, DistributionContext
from compreq.releases import Release, ReleaseSet
from compreq.requirements import (
    OptionalRequirement,
    RequirementSet,
    get_requirement_set,
)


class LazyRelease(ABC):
    """Strategy for computing a `Release` in the context of a distribution."""

    @abstractmethod
    def get_distribution(self) -> str | None:
        """Return the distribution of this `LazyRelease`, if possible.

        Returns `None` if the distribution cannot be determined without resolving the `LazyRelease`.
        """

    @abstractmethod
    async def resolve(self, context: DistributionContext) -> Release:
        """Compute the `Release`."""


@dataclass(order=True, frozen=True)
class EagerLazyRelease(LazyRelease):
    """`LazyRelease` that returns a given constant value."""

    release: Release

    def get_distribution(self) -> str | None:
        return self.release.distribution

    async def resolve(self, context: DistributionContext) -> Release:
        return self.release


AnyRelease: TypeAlias = Release | LazyRelease
"""Type alias for anything that can be converted to a `LazyRelease`."""


def get_lazy_release(release: AnyRelease) -> LazyRelease:
    """Get a `LazyRelease` for the given release-like value."""
    if isinstance(release, Release):
        release = EagerLazyRelease(release)
    if isinstance(release, LazyRelease):
        return release
    raise AssertionError(f"Unknown type of release: {type(release)}")


class LazyReleaseSet(ABC):
    """Strategy for computing a `ReleaseSet` in the context of a distribution."""

    @abstractmethod
    def get_distribution(self) -> str | None:
        """Return the distribution of this `LazyReleaseSet`, if possible.

        Returns `None` if the distribution cannot be determined without resolving the
        `LazyReleaseSet`.
        """

    @abstractmethod
    async def resolve(self, context: DistributionContext) -> ReleaseSet:
        """Compute the `ReleaseSet`."""


@dataclass(order=True, frozen=True)
class EagerLazyReleaseSet(LazyReleaseSet):
    """`LazyReleaseSet` that returns a given constant set of (lazy) releases."""

    releases: frozenset[LazyRelease]

    def get_distribution(self) -> str | None:
        distributions = {r.get_distribution() for r in self.releases}
        if not distributions:
            return None
        (distribution,) = distributions
        return distribution

    async def resolve(self, context: DistributionContext) -> ReleaseSet:
        releases = await asyncio.gather(*[r.resolve(context) for r in self.releases])
        return ReleaseSet(context.distribution, frozenset(releases))


@dataclass(order=True, frozen=True)
class AllLazyReleaseSet(LazyReleaseSet):
    """`LazyReleaseSet` that returns all releases of a given distribution."""

    distribution: str | None
    """
    The distribution to get releases from. If `None`, the distribution of the context is used.
    """

    def get_distribution(self) -> str | None:
        return self.distribution

    async def resolve(self, context: DistributionContext) -> ReleaseSet:
        distribution = self.distribution or context.distribution
        return await context.releases(distribution)


@dataclass(order=True, frozen=True)
class ProdLazyReleaseSet(LazyReleaseSet):
    """`LazyReleaseSet` that filters another `LazyReleaseSet` and only returns the "production"
    releases.
    """

    source: LazyReleaseSet

    def get_distribution(self) -> str | None:
        return self.source.get_distribution()

    async def resolve(self, context: DistributionContext) -> ReleaseSet:
        release_set = await self.source.resolve(context)
        return ReleaseSet(
            distribution=release_set.distribution,
            releases=frozenset(
                r for r in release_set if not (r.version.is_prerelease or r.version.is_devrelease)
            ),
        )


@dataclass(order=True, frozen=True)
class PreLazyReleaseSet(LazyReleaseSet):
    """`LazyReleaseSet` that filters another `LazyReleaseSet` and only returns the "production"
    and "pre-release" releases. (Not development releases.)
    """

    source: LazyReleaseSet

    def get_distribution(self) -> str | None:
        return self.source.get_distribution()

    async def resolve(self, context: DistributionContext) -> ReleaseSet:
        release_set = await self.source.resolve(context)
        return ReleaseSet(
            distribution=release_set.distribution,
            releases=frozenset(r for r in release_set if not r.version.is_devrelease),
        )


@dataclass(order=True, frozen=True)
class SpecifierLazyReleaseSet(LazyReleaseSet):
    """`LazyReleaseSet` that filters another `LazyReleaseSet` based on specifiers."""

    source: LazyReleaseSet
    specifier_set: LazySpecifierSet

    def get_distribution(self) -> str | None:
        return self.source.get_distribution()

    async def resolve(self, context: DistributionContext) -> ReleaseSet:
        release_set, specifier_set = await asyncio.gather(
            self.source.resolve(context),
            self.specifier_set.resolve(context),
        )
        return ReleaseSet(
            distribution=release_set.distribution,
            releases=frozenset(r for r in release_set if r.version in specifier_set),
        )


AnyReleaseSet: TypeAlias = Union[
    None,
    str,
    Specifier,
    "LazySpecifier",
    SpecifierSet,
    "LazySpecifierSet",
    Requirement,
    OptionalRequirement,
    "LazyRequirement",
    Release,
    LazyRelease,
    ReleaseSet,
    LazyReleaseSet,
]
"""Type alias for anything that can be converted to a `LazyReleaseSet`."""


def get_lazy_release_set(release_set: AnyReleaseSet | None) -> LazyReleaseSet:
    """Get a `LazyRelease` for the given release-set-like value."""
    if release_set is None:
        release_set = ProdLazyReleaseSet(AllLazyReleaseSet(None))
    if isinstance(release_set, str):
        release_set = ProdLazyReleaseSet(AllLazyReleaseSet(release_set))
    if isinstance(release_set, (Specifier, LazySpecifier, SpecifierSet)):
        release_set = get_lazy_specifier_set(release_set)
    if isinstance(release_set, LazySpecifierSet):
        release_set = SpecifierLazyReleaseSet(
            ProdLazyReleaseSet(AllLazyReleaseSet(None)),
            release_set,
        )
    if isinstance(release_set, (OptionalRequirement, Requirement)):
        release_set = get_lazy_requirement(release_set)
    if isinstance(release_set, LazyRequirement):
        if release_set.specifier:
            release_set = SpecifierLazyReleaseSet(
                ProdLazyReleaseSet(AllLazyReleaseSet(release_set.distribution)),
                release_set.specifier,
            )
        else:
            release_set = ProdLazyReleaseSet(AllLazyReleaseSet(release_set.distribution))
    if isinstance(release_set, Release):
        release_set = EagerLazyRelease(release_set)
    if isinstance(release_set, LazyRelease):
        release_set = EagerLazyReleaseSet(frozenset([release_set]))
    if isinstance(release_set, ReleaseSet):
        release_set = EagerLazyReleaseSet(frozenset(get_lazy_release(r) for r in release_set))
    if isinstance(release_set, LazyReleaseSet):
        return release_set
    raise AssertionError(f"Unknown type of release set: {type(release_set)}")


class LazyVersion(ABC):
    """Strategy for computing a `Version` in the context of a distribution."""

    @abstractmethod
    async def resolve(self, context: DistributionContext) -> Version:
        """Compute the `Version`."""


@dataclass(order=True, frozen=True)
class EagerLazyVersion(LazyVersion):
    """`LazyVersion` that returns a given constant value."""

    version: Version

    async def resolve(self, context: DistributionContext) -> Version:
        return self.version


@dataclass(order=True, frozen=True)
class ReleaseLazyVersion(LazyVersion):
    """`LazyVersion` that gets the version from a `LazyRelease`."""

    release: LazyRelease

    async def resolve(self, context: DistributionContext) -> Version:
        return (await self.release.resolve(context)).version


AnyVersion: TypeAlias = str | Release | LazyRelease | Version | LazyVersion
"""Type alias for anything that can be converted to a `LazyVersion`."""


def get_lazy_version(version: AnyVersion) -> LazyVersion:
    """Get a `LazyVersion` for the given version-like value."""
    if isinstance(version, str):
        version = Version(version)
    if isinstance(version, Release):
        version = version.version
    if isinstance(version, LazyRelease):
        version = ReleaseLazyVersion(version)
    if isinstance(version, Version):
        version = EagerLazyVersion(version)
    if isinstance(version, LazyVersion):
        return version
    raise AssertionError(f"Unknown type of version: {type(version)}")


class SpecifierOperator(Enum):
    """Enumeration of operators for specifiers."""

    COMPATIBLE = "~="
    NE = "!="
    EQ = "=="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    ARBITRARY_EQ = "==="

    def __lt__(self, other: SpecifierOperator) -> bool:
        return self.value < other.value

    def __gt__(self, other: SpecifierOperator) -> bool:
        return self.value > other.value

    def __le__(self, other: SpecifierOperator) -> bool:
        return self.value <= other.value

    def __ge__(self, other: SpecifierOperator) -> bool:
        return self.value >= other.value


AnySpecifierOperator: TypeAlias = str | SpecifierOperator
"""Type alias for anything that can be converted to a `SpecifierOperator`."""


def get_specifier_operator(op: AnySpecifierOperator) -> SpecifierOperator:
    """Get a `SpecifierOperator` for the given operator-like value."""
    if isinstance(op, str):
        return SpecifierOperator(op)
    if isinstance(op, SpecifierOperator):
        return op
    raise AssertionError(f"Unknown type of operator: {type(op)}")


class LazySpecifier(ABC):
    """Strategy for computing a `Specifier` in the context of a distribution.

    Lazy specifiers can be combined with other specifiers; specifier-sets; and requiremnts using the
    `&` operator::

        lazy_specifier_set = lazy_specifier_1 & lazy_specifier_2
    """

    @abstractmethod
    async def resolve(self, context: DistributionContext) -> Specifier:
        """Compute the `Specifier`."""

    @overload
    def __and__(self, rhs: AnySpecifierSet) -> LazySpecifierSet: ...

    @overload
    def __and__(
        self, rhs: OptionalRequirement | Requirement | LazyRequirement
    ) -> LazyRequirement: ...

    def __and__(self, rhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
        return compose(self, rhs)

    @overload
    def __rand__(self, lhs: AnySpecifierSet) -> LazySpecifierSet: ...

    @overload
    def __rand__(
        self, lhs: OptionalRequirement | Requirement | LazyRequirement
    ) -> LazyRequirement: ...

    def __rand__(self, lhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
        return compose(lhs, self)


@dataclass(order=True, frozen=True)
class EagerLazySpecifier(LazySpecifier):
    op: SpecifierOperator
    version: LazyVersion

    async def resolve(self, context: DistributionContext) -> Specifier:
        op = self.op
        version = await self.version.resolve(context)
        return Specifier(f"{op.value}{version}")


@dataclass(order=True, frozen=True)
class ReleaseLazySpecifier(LazySpecifier):
    release: LazyRelease

    async def resolve(self, context: DistributionContext) -> Specifier:
        release = await self.release.resolve(context)
        return Specifier(f"=={release.version}")


AnySpecifier: TypeAlias = str | Release | LazyRelease | Specifier | LazySpecifier
"""Type alias for anything that can be converted to a `LazySpecifier`."""


def get_lazy_specifier(specifier: AnySpecifier) -> LazySpecifier:
    """Get a `LazySpecifier` for the given specifier-like value."""
    if isinstance(specifier, str):
        specifier = Specifier(specifier)
    if isinstance(specifier, Release):
        specifier = EagerLazyRelease(specifier)
    if isinstance(specifier, LazyRelease):
        specifier = ReleaseLazySpecifier(specifier)
    if isinstance(specifier, Specifier):
        op = get_specifier_operator(specifier.operator)
        version = get_lazy_version(specifier.version)
        specifier = EagerLazySpecifier(op, version)
    if isinstance(specifier, LazySpecifier):
        return specifier
    raise AssertionError(f"Unknown type of specifier: {type(specifier)}")


class LazySpecifierSet(ABC):
    """Strategy for computing a `SpecifierSet` in the context of a distribution.

    Lazy specifier-sets can be combined with specifiers; other specifier-sets; and requiremnts using
    the `&` operator::

        lazy_specifier_set = lazy_specifier_set_1 & lazy_specifier_set_2

    """

    @abstractmethod
    async def resolve(self, context: DistributionContext) -> SpecifierSet:
        """Compute the `SpecifierSet`."""

    @overload
    def __and__(self, rhs: AnySpecifierSet) -> LazySpecifierSet: ...

    @overload
    def __and__(
        self, rhs: OptionalRequirement | Requirement | LazyRequirement
    ) -> LazyRequirement: ...

    def __and__(self, rhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
        return compose(self, rhs)

    @overload
    def __rand__(self, lhs: AnySpecifierSet) -> LazySpecifierSet: ...

    @overload
    def __rand__(
        self, lhs: OptionalRequirement | Requirement | LazyRequirement
    ) -> LazyRequirement: ...

    def __rand__(self, lhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
        return compose(lhs, self)


@dataclass(frozen=True)
class EagerLazySpecifierSet(LazySpecifierSet):
    specifiers: frozenset[LazySpecifier]

    async def resolve(self, context: DistributionContext) -> SpecifierSet:
        specifiers = await asyncio.gather(*[s.resolve(context) for s in self.specifiers])
        return SpecifierSet(",".join(str(s) for s in specifiers))


@dataclass(frozen=True)
class CompositeLazySpecifierSet(LazySpecifierSet):
    specifiers: frozenset[LazySpecifierSet]

    async def resolve(self, context: DistributionContext) -> SpecifierSet:
        specifiers = await asyncio.gather(*[s.resolve(context) for s in self.specifiers])
        return SpecifierSet(",".join(str(s) for s in specifiers))


AnySpecifierSet: TypeAlias = (
    str | Release | LazyRelease | Specifier | LazySpecifier | SpecifierSet | LazySpecifierSet
)
"""Type alias for anything that can be converted to a `LazySpecifierSet`."""


def get_lazy_specifier_set(specifier_set: AnySpecifierSet) -> LazySpecifierSet:
    """Get a `LazySpecifierSet` for the given specifier-set-like value."""
    if isinstance(specifier_set, str):
        specifier_set = SpecifierSet(specifier_set)
    if isinstance(specifier_set, (Release, LazyRelease, Specifier)):
        specifier_set = get_lazy_specifier(specifier_set)
    if isinstance(specifier_set, LazySpecifier):
        specifier_set = EagerLazySpecifierSet(frozenset([specifier_set]))
    if isinstance(specifier_set, SpecifierSet):
        specifier_set = EagerLazySpecifierSet(
            frozenset(get_lazy_specifier(s) for s in specifier_set)
        )
    if isinstance(specifier_set, LazySpecifierSet):
        return specifier_set
    raise AssertionError(f"Unknown type of specifier set: {type(specifier_set)}")


AnyMarker: TypeAlias = str | Marker
"""Type alias for anything that can be converted to a `Marker`."""


def get_marker(marker: AnyMarker) -> Marker:
    """Get a `Marker` for the given marker-like value."""
    if isinstance(marker, str):
        marker = Marker(marker)
    if isinstance(marker, Marker):
        return marker
    raise AssertionError(f"Unknown type of marker: {type(marker)}")


@dataclass(order=True, frozen=True)
class LazyRequirement:
    """Strategy for computing a `Requirement` in a context.

    A `LazyRequirement` can be in a partially configured state. To be valid a `LazyRequirement`
    must:

    * Have a `distribution` configured.
    * Cannot have both a `url` and a `specifier`.

    Lazy requiremnts can be combined with specifiers; specifier-sets; and other requiremnts using
    the `&` operator::

        lazy_requirement = lazy_requirement_1 & lazy_requirement_2
    """

    distribution: str | None
    """The required distribution. Required."""

    url: str | None
    """
    The url to download the distribution at. Use:

    * file:///... to refer to local files.
    * git+https://... to refer to git repositories.

    Mutually exclusive with `specifier`.
    """

    extras: frozenset[str]
    """Set of extras to install."""

    specifier: LazySpecifierSet | None
    """
    Specification of which versions of the distribution are valid.

    Mutually exclusize with `url`.
    """

    marker: Marker | None
    """Marker for specifying when this requirement should be used."""

    optional: bool | None
    """
    Whether this requirement is optional.

    Currently only used by Poetry.
    """

    def __post_init__(self) -> None:
        assert (self.url is None) or (self.specifier is None), (
            "A requirement cannot have both a url and a specifier."
            f" Found: {self.url}, {self.specifier}."
        )

    def __and__(self, rhs: AnyRequirement) -> LazyRequirement:
        return compose(self, rhs)

    def __rand__(self, lhs: AnyRequirement) -> LazyRequirement:
        return compose(lhs, self)

    def assert_valid(self) -> None:
        assert self.distribution, (
            f"A requirement must have the distribution name set. Found: {self.distribution}."
        )

    async def resolve(self, context: Context) -> OptionalRequirement:
        """Compute the `Requirement`."""
        self.assert_valid()
        assert self.distribution

        tokens = []
        tokens.append(self.distribution)

        if self.extras:
            formatted_extras = ",".join(sorted(self.extras))
            tokens.append(f"[{formatted_extras}]")

        distribution_context = context.for_distribution(self.distribution)
        specifier = (
            (await self.specifier.resolve(distribution_context))
            if self.specifier
            else SpecifierSet()
        )
        tokens.append(str(specifier))

        if self.url:
            tokens.append(f"@ {self.url}")
            if self.marker:
                tokens.append(" ")

        if self.marker:
            tokens.append(f"; {self.marker}")

        optional = self.optional or False

        return OptionalRequirement(Requirement("".join(tokens)), optional)


EMPTY_REQUIREMENT: Final[LazyRequirement] = LazyRequirement(
    distribution=None,
    url=None,
    extras=frozenset(),
    specifier=None,
    marker=None,
    optional=None,
)
"""
A `LazyRequirement` without any values set.

Useful for constructing partial requirements::

    from dataclasses import replace

    replace(EMPTY_REQUIREMENT, distribution="foo.bar")

"""


AnyRequirement: TypeAlias = (
    str
    | Release
    | LazyRelease
    | Specifier
    | LazySpecifier
    | SpecifierSet
    | LazySpecifierSet
    | OptionalRequirement
    | Requirement
    | LazyRequirement
)
"""Type alias for anything that can be converted to a `LazyRequirement`."""


def get_lazy_requirement(requirement: AnyRequirement) -> LazyRequirement:
    """Get a `LazyRequirement` for the given requirement-like value."""
    if isinstance(requirement, str):
        requirement = Requirement(requirement)
    if isinstance(requirement, Release):
        requirement = EagerLazyRelease(requirement)
    if isinstance(requirement, LazyRelease):
        distribution = requirement.get_distribution()
        assert distribution is not None, requirement
        requirement = replace(
            EMPTY_REQUIREMENT,
            distribution=distribution,
            specifier=get_lazy_specifier_set(requirement),
        )
    if isinstance(requirement, (Specifier, LazySpecifier, SpecifierSet)):
        requirement = get_lazy_specifier_set(requirement)
    if isinstance(requirement, LazySpecifierSet):
        requirement = replace(EMPTY_REQUIREMENT, specifier=requirement)
    if isinstance(requirement, OptionalRequirement):
        requirement = LazyRequirement(
            distribution=requirement.name,
            url=requirement.url,
            extras=frozenset(requirement.extras),
            specifier=(
                get_lazy_specifier_set(requirement.specifier) if requirement.specifier else None
            ),
            marker=requirement.marker,
            optional=requirement.optional,
        )
    if isinstance(requirement, Requirement):
        requirement = LazyRequirement(
            distribution=requirement.name,
            url=requirement.url,
            extras=frozenset(requirement.extras),
            specifier=(
                get_lazy_specifier_set(requirement.specifier) if requirement.specifier else None
            ),
            marker=requirement.marker,
            optional=None,
        )
    if isinstance(requirement, LazyRequirement):
        return requirement
    raise AssertionError(f"Unknown type of requirement: {type(requirement)}")


@overload
def compose(
    lhs: str | Specifier | LazySpecifier | SpecifierSet | LazySpecifierSet,
    rhs: str | Specifier | LazySpecifier | SpecifierSet | LazySpecifierSet,
) -> LazySpecifierSet: ...


@overload
def compose(
    lhs: AnyRequirement,
    rhs: Release | LazyRelease | OptionalRequirement | Requirement | LazyRequirement,
) -> LazyRequirement: ...


@overload
def compose(
    lhs: Release | LazyRelease | OptionalRequirement | Requirement | LazyRequirement,
    rhs: AnyRequirement,
) -> LazyRequirement: ...


def compose(lhs: AnyRequirement, rhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
    """Combine two specifier-, specifier-set- or requirement-like values into a `LazySpecifierSet` or
    `LazyRequirement`.

    If either of the arguments are a requirement, the result is `LazyRequirement`. If neither
    argument is a requirement the result is a `LazySpecifierSet`.

    """
    if isinstance(
        lhs, (Release, LazyRelease, OptionalRequirement, Requirement, LazyRequirement)
    ) or isinstance(rhs, (Release, LazyRelease, OptionalRequirement, Requirement, LazyRequirement)):
        lhr = get_lazy_requirement(lhs)
        rhr = get_lazy_requirement(rhs)

        assert (
            lhr.distribution is None
            or rhr.distribution is None
            or lhr.distribution == rhr.distribution
        ), (
            "A requirement can have at most one distribution name."
            f" Found: {lhr.distribution} and {rhr.distribution}."
        )
        distribution = lhr.distribution or rhr.distribution

        assert lhr.url is None or rhr.url is None or lhr.url == rhr.url, (
            f"A requirement can have at most one url. Found: {lhr.url} and {rhr.url}."
        )
        url = lhr.url or rhr.url

        extras = frozenset(chain(lhr.extras, rhr.extras))

        if lhr.specifier is None:
            specifier = rhr.specifier
        elif rhr.specifier is None:
            specifier = lhr.specifier
        else:
            specifier = compose(lhr.specifier, rhr.specifier)

        marker: Marker | None
        if lhr.marker is None:
            marker = rhr.marker
        elif rhr.marker is None:
            marker = lhr.marker
        elif lhr.marker == rhr.marker:
            marker = lhr.marker
        else:
            marker = Marker(f"({lhr.marker}) and ({rhr.marker})")

        assert lhr.optional is None or rhr.optional is None or lhr.optional == rhr.optional, (
            f"A requirement can have at most one optional. Found: {lhr.optional} and {rhr.optional}."
        )
        optional = lhr.optional or rhr.optional

        return LazyRequirement(
            distribution=distribution,
            url=url,
            extras=extras,
            specifier=specifier,
            marker=marker,
            optional=optional,
        )
    else:
        lhss = get_lazy_specifier_set(lhs)
        rhss = get_lazy_specifier_set(rhs)
        if isinstance(lhss, EagerLazySpecifierSet) and isinstance(rhss, EagerLazySpecifierSet):
            return EagerLazySpecifierSet(frozenset(chain(lhss.specifiers, rhss.specifiers)))
        specifiers: list[LazySpecifierSet] = []
        if isinstance(lhss, CompositeLazySpecifierSet):
            specifiers.extend(lhss.specifiers)
        else:
            specifiers.append(lhss)
        if isinstance(rhss, CompositeLazySpecifierSet):
            specifiers.extend(rhss.specifiers)
        else:
            specifiers.append(rhss)
        return CompositeLazySpecifierSet(frozenset(specifiers))


class LazyRequirementSet(ABC):
    """Strategy for computing a `RequirementSet` in a context."""

    @abstractmethod
    async def resolve(self, context: Context) -> RequirementSet:
        """Compute the `RequirementSet`."""


@dataclass(order=True, frozen=True)
class EagerLazyRequirementSet(LazyRequirementSet):
    """`LazyRequirementSet` that returns a given constant value."""

    requirements: frozenset[LazyRequirement]

    async def resolve(self, context: Context) -> RequirementSet:
        requirements = await asyncio.gather(*[r.resolve(context) for r in self.requirements])
        return get_requirement_set(requirements)


AnyRequirementSet: TypeAlias = (
    str
    | Release
    | LazyRelease
    | Specifier
    | LazySpecifier
    | SpecifierSet
    | LazySpecifierSet
    | OptionalRequirement
    | Requirement
    | LazyRequirement
    | Mapping[str, AnyRequirement]
    | Iterable[AnyRequirement]
    | RequirementSet
    | LazyRequirementSet
)
"""Type alias for anything that can be converted to a `LazyRequirementSet`."""


def get_lazy_requirement_set(requirement_set: AnyRequirementSet) -> LazyRequirementSet:
    """Get a `LazyRequirementSet` for the given requirement-set-like value."""
    if isinstance(
        requirement_set,
        (
            str,
            Release,
            LazyRelease,
            Specifier,
            LazySpecifier,
            SpecifierSet,
            LazySpecifierSet,
            OptionalRequirement,
            Requirement,
        ),
    ):
        requirement_set = get_lazy_requirement(requirement_set)
    if isinstance(requirement_set, LazyRequirement):
        requirement_set = EagerLazyRequirementSet(frozenset([requirement_set]))
    if isinstance(requirement_set, Mapping):
        requirement_set = requirement_set.values()
    if isinstance(requirement_set, Iterable):
        requirement_set = EagerLazyRequirementSet(
            frozenset(get_lazy_requirement(r) for r in requirement_set)
        )
    if isinstance(requirement_set, LazyRequirementSet):
        return requirement_set
    raise AssertionError(f"Unknown type of requirement set: {type(requirement_set)}")
