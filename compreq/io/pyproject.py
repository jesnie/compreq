from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from packaging.specifiers import SpecifierSet
from tomlkit import dump, dumps, load
from typing_extensions import Self

from compreq.classifiers import set_python_classifiers
from compreq.lazy import AnyReleaseSet, AnyRequirementSet, AnySpecifierSet
from compreq.paths import AnyPath
from compreq.requirements import (
    RequirementSet,
    get_requirement_set,
)
from compreq.roots import CompReq


class PyprojectFile:
    """Wrapper around a generic `pyproject.toml`.

    Usage::

        with PyprojectFile.open() as pyproject:
            pyproject.toml[...] = ...
    """

    def __init__(self, path: AnyPath) -> None:
        self.path = Path(path)
        with open(self.path, "rt", encoding="utf-8") as fp:
            self.toml: Any = load(fp)

    def close(self) -> None:
        with open(self.path, "wt", encoding="utf-8") as fp:
            dump(self.toml, fp)

    @classmethod
    @contextmanager
    def open(cls, path: AnyPath = "pyproject.toml") -> Iterator[Self]:
        f = cls(path)
        yield f
        f.close()

    def __str__(self) -> str:
        return dumps(self.toml)

    def get_requirements(
        self, *, group: str | None = None, extra: str | None = None
    ) -> RequirementSet:
        """
        Get the given `group` or `extra` of requirements.

        If `group` and `extra` is `None` the main group is returned.
        """
        return get_requirement_set(self._get_dependencies(group, extra))

    def set_requirements(
        self,
        cr: CompReq,
        requirement_set: AnyRequirementSet,
        *,
        group: str | None = None,
        extra: str | None = None,
    ) -> None:
        """
        Set the given `group` or `extra` of requirements.

        If `group` and `extra` is `None` the main group is returned.
        """
        requirements = list(cr.resolve_requirement_set(requirement_set).values())
        assert not any(r.optional for r in requirements)
        requirements_toml = self._get_dependencies(group, extra)
        requirements_toml.clear()
        requirements_toml.extend(str(r.requirement) for r in requirements)
        requirements_toml.multiline(True)

    def _get_project(self) -> Any:
        return self.toml["project"]

    def _get_dependencies(self, group: str | None, extra: str | None) -> Any:
        assert (group is None) or (extra is None), (group, extra)
        if group is not None:
            return self.toml["dependency-groups"][group]
        elif extra is not None:
            return self._get_project()["optional-dependencies"][extra]
        else:
            return self._get_project()["dependencies"]

    def get_requires_python(self) -> SpecifierSet:
        """Read the `project.requires_python` field."""
        return SpecifierSet(self._get_project()["requires-python"])

    def set_requires_python(self, cr: CompReq, specifier: AnySpecifierSet) -> None:
        """Write the `project.requires_python` field."""
        self._get_project()["requires-python"] = str(cr.resolve_specifier_set("python", specifier))

    def get_classifiers(self) -> Sequence[str]:
        """Get the distribution classifiers. (https://pypi.org/classifiers/)"""
        return list(self._get_project()["classifiers"])

    def set_classifiers(self, classifiers: Sequence[str]) -> None:
        """Set the distribution classifiers. (https://pypi.org/classifiers/)"""
        toml = self._get_project()["classifiers"]
        toml.clear()
        toml.extend(classifiers)
        toml.multiline(True)

    def set_python_classifiers(
        self, cr: CompReq, python_releases: AnyReleaseSet | None = None
    ) -> None:
        """Replace python distribution classifiers (https://pypi.org/classifiers/) with those
        corresponding to `python_releases`.
        """
        self.set_classifiers(set_python_classifiers(self.get_classifiers(), cr, python_releases))
