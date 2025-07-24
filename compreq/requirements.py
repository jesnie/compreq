from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Set
from dataclasses import dataclass
from typing import NewType, TypeAlias

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

_Unset = NewType("_Unset", object)
_UNSET = _Unset(object())


@dataclass(order=True, frozen=True)
class OptionalRequirement:
    """Extension of `Requirement` to support being optional."""

    requirement: Requirement
    optional: bool

    @property
    def name(self) -> str:
        return self.requirement.name

    @property
    def url(self) -> str | None:
        return self.requirement.url

    @property
    def extras(self) -> Set[str]:
        return self.requirement.extras

    @property
    def specifier(self) -> SpecifierSet:
        return self.requirement.specifier

    @property
    def marker(self) -> Marker | None:
        return self.requirement.marker


AnyOptionalRequirement: TypeAlias = str | Requirement | OptionalRequirement


def get_optional_requirement(requirement: AnyOptionalRequirement) -> OptionalRequirement:
    if isinstance(requirement, str):
        requirement = Requirement(requirement)
    if isinstance(requirement, Requirement):
        requirement = OptionalRequirement(requirement, optional=False)
    if isinstance(requirement, OptionalRequirement):
        return requirement
    raise AssertionError(f"Unknown type of optional requirement: {type(requirement)}")


def make_requirement(
    base: OptionalRequirement | _Unset = _UNSET,
    *,
    distribution: str | _Unset = _UNSET,
    url: str | None | _Unset = _UNSET,
    extras: set[str] | _Unset = _UNSET,
    specifier: SpecifierSet | _Unset = _UNSET,
    marker: Marker | None | _Unset = _UNSET,
    optional: bool | _Unset = _UNSET,
) -> OptionalRequirement:
    requirement = Requirement.__new__(Requirement)

    if isinstance(distribution, str):
        requirement.name = distribution
    else:
        assert isinstance(base, OptionalRequirement)
        requirement.name = base.name

    if (url is None) or isinstance(url, str):
        requirement.url = url
    elif isinstance(base, OptionalRequirement):
        requirement.url = base.url
    else:
        requirement.url = None

    if isinstance(extras, set):
        requirement.extras = extras
    elif isinstance(base, OptionalRequirement):
        requirement.extras = set(base.extras)
    else:
        requirement.extras = set()

    if isinstance(specifier, SpecifierSet):
        requirement.specifier = specifier
    elif isinstance(base, OptionalRequirement):
        requirement.specifier = base.specifier
    else:
        requirement.specifier = SpecifierSet()

    if (marker is None) or isinstance(marker, Marker):
        requirement.marker = marker
    elif isinstance(base, OptionalRequirement):
        requirement.marker = base.marker
    else:
        requirement.marker = None

    if isinstance(optional, bool):
        result_optional = optional
    elif isinstance(base, OptionalRequirement):
        result_optional = base.optional
    else:
        result_optional = False

    return OptionalRequirement(requirement, result_optional)


@dataclass(frozen=True)
class RequirementSet(Mapping[str, OptionalRequirement]):
    """A set of requirements.

    Despite the name this functions more like a mapping from distribution name to the requirements
    for that distribution.
    """

    requirements: Mapping[str, OptionalRequirement]

    def __getitem__(self, key: str) -> OptionalRequirement:
        return self.requirements[key]

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self.requirements))

    def __len__(self) -> int:
        return len(self.requirements)


AnyRequirementSet_: TypeAlias = (
    AnyOptionalRequirement | Mapping[str, AnyOptionalRequirement] | Iterable[AnyOptionalRequirement]
)


def get_requirement_set(requirement_set: AnyRequirementSet_) -> RequirementSet:
    if isinstance(requirement_set, RequirementSet):
        return requirement_set
    if isinstance(requirement_set, (str, Requirement, OptionalRequirement)):
        requirement_set = [requirement_set]
    if isinstance(requirement_set, Mapping):
        requirement_set = requirement_set.values()
    return RequirementSet({(o := get_optional_requirement(r)).name: o for r in requirement_set})
