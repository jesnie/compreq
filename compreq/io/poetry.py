from collections.abc import Sequence
from typing import Any

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from tomlkit import inline_table

from compreq.classifiers import set_python_classifiers
from compreq.io.pyproject import PyprojectFile
from compreq.lazy import AnyReleaseSet, AnyRequirementSet
from compreq.levels import REL_MAJOR
from compreq.requirements import (
    OptionalRequirement,
    RequirementSet,
    get_requirement_set,
)
from compreq.roots import CompReq
from compreq.rounding import ceil


class PoetryPyprojectFile(PyprojectFile):
    """Wrapper around a `pyproject.toml` using Poetry.

    Usage::

        with PoetryPyprojectFile.open() as pyproject:
            pyproject.set_requirements(...)
    """

    def get_requirements(
        self, *, group: str | None = None, extra: str | None = None
    ) -> RequirementSet:
        """
        Get the given `group` or `extra` of requirements.

        If `group` and `extra` is `None` the main group is returned.
        """
        return get_requirement_set(
            self._parse_requirement(distribution, toml)
            for distribution, toml in self._get_dependencies(group, extra).items()
        )

    def _parse_requirement(self, distribution: str, toml: Any) -> OptionalRequirement:
        requirement = Requirement.__new__(Requirement)
        requirement.name = distribution
        requirement.url = None
        requirement.extras = set()
        requirement.specifier = SpecifierSet()
        requirement.marker = None
        optional = False

        if isinstance(toml, dict):
            if "url" in toml:
                requirement.url = toml["url"]
            if "path" in toml:
                requirement.url = f"file://{toml['path']}"
            if "git" in toml:
                requirement.url = f"git+{toml['git']}"
            if "extras" in toml:
                requirement.extras = set(toml["extras"])
            if "version" in toml:
                requirement.specifier = self._parse_specifier_set(toml["version"])
            if "markers" in toml:
                requirement.marker = Marker(toml["markers"])
            if "optional" in toml:
                optional = toml["optional"]
        else:
            requirement.specifier = self._parse_specifier_set(toml)

        return OptionalRequirement(requirement, optional)

    def _parse_specifier_set(self, specifier_set: str) -> SpecifierSet:
        result = SpecifierSet()
        for specifier in specifier_set.split(","):
            if specifier.startswith("^"):
                version = Version(specifier[1:])
                upper = ceil(REL_MAJOR, version, keep_trailing_zeros=True)
                result &= SpecifierSet(f"<{upper},>={version}")
            elif specifier.startswith("~"):
                result &= SpecifierSet(f"~={specifier[1:]}")
            elif specifier.startswith(("<", ">", "!=")):
                result &= SpecifierSet(specifier)
            else:
                result &= SpecifierSet(f"=={specifier}")
        return result

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
        requirements = cr.resolve_requirement_set(requirement_set)
        requirements_toml = self._get_dependencies(group, extra)
        requirements_toml.clear()
        for r in requirements.values():
            requirements_toml[r.name] = self._format_requirement(r)

    def _format_requirement(self, requirement: OptionalRequirement) -> Any:
        result = inline_table()

        if requirement.url is not None:
            url = requirement.url
            if url.startswith("file://"):
                result["path"] = url[7:]
            elif url.startswith("git+"):
                result["git"] = url[4:]
            else:
                result["url"] = url
        if requirement.extras:
            result["extras"] = sorted(requirement.extras)
        if requirement.specifier:
            result["version"] = self._format_specifier_set(requirement.specifier)
        if requirement.marker is not None:
            result["markers"] = str(requirement.marker)
        if requirement.optional:
            result["optional"] = requirement.optional

        return result if list(result) != ["version"] else result["version"]

    def _format_specifier_set(self, specifier_set: SpecifierSet) -> str:
        specifiers = []
        for specifier in specifier_set:
            if specifier.operator == "==":
                specifiers.append(specifier.version)
            elif specifier.operator == "~=":
                specifiers.append(f"~{specifier.version}")
            else:
                specifiers.append(str(specifier))
        return ",".join(sorted(specifiers))

    def _get_poetry(self) -> Any:
        return self.toml["tool"]["poetry"]

    def _get_dependencies(self, group: str | None, extra: str | None) -> Any:
        assert extra is None, (
            "extra is currently not supported for Poetry. Instead, make the dependencies Optional."
        )
        if group is None:
            return self._get_poetry()["dependencies"]
        else:
            return self._get_poetry()["group"][group]["dependencies"]

    def get_classifiers(self) -> Sequence[str]:
        """Get the distribution classifiers. (https://pypi.org/classifiers/)"""
        return list(self._get_poetry()["classifiers"])

    def set_classifiers(self, classifiers: Sequence[str]) -> None:
        """Set the distribution classifiers. (https://pypi.org/classifiers/)"""
        toml = self._get_poetry()["classifiers"]
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
