from __future__ import annotations

import asyncio
from typing import NoReturn, overload

from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from compreq.contexts import Context, DefaultContext
from compreq.lazy import (
    AnyRelease,
    AnyReleaseSet,
    AnyRequirement,
    AnyRequirementSet,
    AnySpecifier,
    AnySpecifierSet,
    AnyVersion,
    get_lazy_release,
    get_lazy_release_set,
    get_lazy_requirement,
    get_lazy_requirement_set,
    get_lazy_specifier,
    get_lazy_specifier_set,
    get_lazy_version,
)
from compreq.releases import Release, ReleaseSet
from compreq.requirements import OptionalRequirement, RequirementSet


class CompReq:
    """Factory for resolving lazy objects."""

    @overload
    def __init__(
        self,
        python_specifier: SpecifierSet | str,
        *,
        default_python: Version | str | None = None,
        context: Context,
    ) -> NoReturn: ...

    @overload
    def __init__(
        self,
        python_specifier: SpecifierSet | str,
        *,
        default_python: Version | str | None = None,
        context: None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        python_specifier: None = None,
        *,
        default_python: None = None,
        context: Context,
    ) -> None: ...

    @overload
    def __init__(
        self,
        python_specifier: None = None,
        *,
        default_python: None = None,
        context: None = None,
    ) -> NoReturn: ...

    def __init__(
        self,
        python_specifier: SpecifierSet | str | None = None,
        *,
        default_python: Version | str | None = None,
        context: Context | None = None,
    ) -> None:
        """:param python_specifier: Allowed python versions.
            You must set `context` xor `python_specifier`.
        :param default_python: Which version of python to use when resolving requiremnts.
            Can only be set when `python_specifier` is set.
        :param context: Context to use. If `None` a default is created.
            You must set `context` xor `python_specifier`.
        """
        assert (context is None) != (python_specifier is None), (
            "Must set exactly one of `context` and `python_specifier`."
            f" Found: {context=}, {python_specifier=}"
        )
        if default_python is not None:
            assert python_specifier is not None, (
                "`default_python` can only be set when `python_specifier` is set."
                f" Found: {python_specifier=}, {default_python=}"
            )
        if context is None:
            assert python_specifier is not None, python_specifier
            context = DefaultContext(python_specifier, default_python=default_python)
        assert context is not None
        self._context = context

    def for_python(
        self,
        python_specifier: AnySpecifierSet,
        *,
        default_python: AnyVersion | None = None,
    ) -> CompReq:
        python_specifier = self.resolve_specifier_set("python", python_specifier)
        assert isinstance(python_specifier, SpecifierSet)
        if default_python is not None:
            default_python = self.resolve_version("python", default_python)
        assert (default_python is None) or isinstance(default_python, Version)

        return CompReq(
            context=self._context.for_python(
                python_specifier=python_specifier,
                default_python=default_python,
            ),
        )

    def resolve_release(self, distribution: str, release: AnyRelease) -> Release:
        context = self._context.for_distribution(distribution)
        future = get_lazy_release(release).resolve(context)
        return asyncio.run(future)

    def resolve_release_set(self, distribution: str, release_set: AnyReleaseSet) -> ReleaseSet:
        context = self._context.for_distribution(distribution)
        future = get_lazy_release_set(release_set).resolve(context)
        return asyncio.run(future)

    def resolve_version(self, distribution: str, version: AnyVersion) -> Version:
        context = self._context.for_distribution(distribution)
        future = get_lazy_version(version).resolve(context)
        return asyncio.run(future)

    def resolve_specifier(self, distribution: str, specifier: AnySpecifier) -> Specifier:
        context = self._context.for_distribution(distribution)
        future = get_lazy_specifier(specifier).resolve(context)
        return asyncio.run(future)

    def resolve_specifier_set(
        self,
        distribution: str,
        specifier_set: AnySpecifierSet,
    ) -> SpecifierSet:
        context = self._context.for_distribution(distribution)
        future = get_lazy_specifier_set(specifier_set).resolve(context)
        return asyncio.run(future)

    def resolve_requirement(self, requirement: AnyRequirement) -> OptionalRequirement:
        future = get_lazy_requirement(requirement).resolve(self._context)
        return asyncio.run(future)

    def resolve_requirement_set(self, requirement_set: AnyRequirementSet) -> RequirementSet:
        future = get_lazy_requirement_set(requirement_set).resolve(self._context)
        return asyncio.run(future)
