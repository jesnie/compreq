from collections.abc import Set
from dataclasses import dataclass

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from compreq.levels import IntLevel
from compreq.rounding import ceil


@dataclass(order=True, frozen=True)
class Bounds:
    """Bounds of versions, extracted from a `SpecfierSet`."""

    specifier_set: SpecifierSet
    """The source `SpecifierSet`."""

    upper: Version | None
    """Upper bound on versions. `None` if there is no upper bound."""

    upper_inclusive: bool
    """Whether the upper bound is inclusive."""

    lower: Version | None
    """Lower bound on versions. `None` if there is no lower bound."""

    lower_inclusive: bool
    """Whether the lower bound is inclusive."""

    exclusions: Set[Version]
    """Set of specific versions that are disallowed."""

    def minimal_specifier_set(self, exclusions: bool = True) -> SpecifierSet:
        """Create a new (minimal) specifier set from these bounds.

        :param exclusions: Whether to excluded specific versions.
        """
        return self.upper_specifier_set(False) & self.lower_specifier_set(exclusions)

    def upper_specifier_set(self, exclusions: bool = True) -> SpecifierSet:
        """Create a new specifier set from the upper bounds.

        :param exclusions: Whether to excluded specific versions.
        """
        result = SpecifierSet()
        if self.upper is not None:
            if self.upper_inclusive:
                result &= SpecifierSet(f"<={self.upper!s}")
            else:
                result &= SpecifierSet(f"<{self.upper!s}")
        if exclusions:
            result &= self.exclusions_specifier_set()
        return result

    def lower_specifier_set(self, exclusions: bool = True) -> SpecifierSet:
        """Create a new specifier set from the lower bounds.

        :param exclusions: Whether to excluded specific versions.
        """
        result = SpecifierSet()
        if self.lower is not None:
            if self.lower_inclusive:
                result &= SpecifierSet(f">={self.lower!s}")
            else:
                result &= SpecifierSet(f">{self.lower!s}")
        if exclusions:
            result &= self.exclusions_specifier_set()
        return result

    def exclusions_specifier_set(self) -> SpecifierSet:
        """Create a new specifier set, only excluding specific versions."""
        return SpecifierSet(",".join(f"!={v!s}" for v in self.exclusions))


def get_bounds(specifier_set: SpecifierSet) -> Bounds:
    """Extracts bounds from a `SpecifierSet`."""
    upper: Version | None = None
    upper_inclusive: bool = False
    lower: Version | None = None
    lower_inclusive: bool = False
    exclusions: set[Version] = set()
    for specifier in specifier_set:
        version = Version(specifier.version)
        match specifier.operator:
            case ">":
                if lower is None or version >= lower:
                    lower = version
                    lower_inclusive = False
            case ">=":
                if lower is None or version > lower:
                    lower = version
                    lower_inclusive = True
            case "<":
                if upper is None or version <= upper:
                    upper = version
                    upper_inclusive = False
            case "<=":
                if upper is None or version < upper:
                    upper = version
                    upper_inclusive = True
            case "==":
                if lower is None or version > lower:
                    lower = version
                    lower_inclusive = True
                if upper is None or version < upper:
                    upper = version
                    upper_inclusive = True
            case "~=":
                vupper = ceil(IntLevel(-1), version, keep_trailing_zeros=False)
                if upper is None or vupper <= upper:
                    upper = vupper
                    upper_inclusive = False
                if lower is None or version > lower:
                    lower = version
                    lower_inclusive = True
            case "!=":
                exclusions.add(version)
            case _:
                raise AssertionError(f"Unknown specifier: {specifier}")

    if upper:
        if upper_inclusive and upper in exclusions:
            upper_inclusive = False

        if upper_inclusive:
            exclusions = {e for e in exclusions if e <= upper}
        else:
            exclusions = {e for e in exclusions if e < upper}

    if lower:
        if lower_inclusive and lower in exclusions:
            lower_inclusive = False

        if lower_inclusive:
            exclusions = {e for e in exclusions if e >= lower}
        else:
            exclusions = {e for e in exclusions if e > lower}

    if upper is not None and lower is not None:
        if upper_inclusive and lower_inclusive:
            assert lower <= upper, f"Empty specifier set: {specifier_set}"
        else:
            assert lower < upper, f"Empty specifier set: {specifier_set}"

    return Bounds(specifier_set, upper, upper_inclusive, lower, lower_inclusive, exclusions)
