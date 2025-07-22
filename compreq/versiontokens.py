from __future__ import annotations

from compreq.lazy import (
    AnySpecifierOperator,
    AnyVersion,
    EagerLazySpecifier,
    LazySpecifier,
    SpecifierOperator,
    get_lazy_version,
    get_specifier_operator,
)


class VersionToken:
    """
    Factory for creating version specifiers. See: `compreq.lazy`.
    """

    def require(self, op: AnySpecifierOperator, version: AnyVersion) -> LazySpecifier:
        op = get_specifier_operator(op)
        version = get_lazy_version(version)
        return EagerLazySpecifier(op, version)

    def __call__(self, op: AnySpecifierOperator, version: AnyVersion) -> LazySpecifier:
        return self.require(op, version)

    def compatible(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.COMPATIBLE, version)

    def exclude(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.NE, version)

    def ne(self, version: AnyVersion) -> LazySpecifier:
        return self.exclude(version)

    def __ne__(self, version: AnyVersion) -> LazySpecifier:  # type: ignore[override]
        return self.exclude(version)

    def match(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.EQ, version)

    def eq(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.EQ, version)

    def __eq__(self, version: AnyVersion) -> LazySpecifier:  # type: ignore[override]
        return self.require(SpecifierOperator.EQ, version)

    def less(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.LT, version)

    def lt(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.LT, version)

    def __lt__(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.LT, version)

    def greater(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.GT, version)

    def gt(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.GT, version)

    def __gt__(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.GT, version)

    def less_or_equal(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.LE, version)

    def le(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.LE, version)

    def __le__(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.LE, version)

    def greater_or_equal(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.GE, version)

    def ge(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.GE, version)

    def __ge__(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.GE, version)

    def arbitrary_equal(self, version: AnyVersion) -> LazySpecifier:
        return self.require(SpecifierOperator.ARBITRARY_EQ, version)
