import asyncio
from pathlib import Path
from unittest.mock import MagicMock

from packaging.specifiers import SpecifierSet

import compreq as cr
from compreq.lazy import AnySpecifierSet
from tests.utils import fake_release_set

PYPROJECT_CONTENTS = """
[project]
name = "compreq"
version = "0.1.0"
requires-python = "<4,>=3.12"

dependencies = [
    "dist1!=1.2.5,<2.0.0,>=1.2.3",
    "dist2<=1.9.0,>1.2.3",
    "dist3==1.2.5",
    "dist4~=1.2",
    "distextra[extra1,extra2]==1.2.3",
    "distmarker>=1.2.3; platform_system != 'Darwin' or platform_machine != 'arm64'",
]

[project.optional-dependencies]
test_extra = [
    "dist-extra1<3.0.0,>=2.1.0",
]

[dependency-groups]
dev = [
    "dist-dev1<2.0.0,>=1.2.3",
]
"""

PYPROJECT_CONTENTS_AFTER = """
[project]
name = "compreq"
version = "0.1.0"
requires-python = "<4,>=3.12"

dependencies = [
    "dist1!=1.2.5,<2.0.0,>=1.2.3",
    "dist2<=1.9.0,>1.2.3",
    "dist3==1.2.5",
    "dist4~=1.2",
    "distextra[extra1,extra2]==1.2.3",
    "distmarker>=1.2.3; platform_system != \\"Darwin\\" or platform_machine != \\"arm64\\"",
]

[project.optional-dependencies]
test_extra = [
    "dist-extra1<3.0.0,>=2.1.0",
]

[dependency-groups]
dev = [
    "dist-dev1<2.0.0,>=1.2.3",
]
"""

MAIN_REQUIREMENTS = cr.get_requirement_set(
    [
        "dist1!=1.2.5,<2.0.0,>=1.2.3",
        "dist2<=1.9.0,>1.2.3",
        "dist3==1.2.5",
        "dist4~=1.2",
        "distextra[extra1, extra2]==1.2.3",
        "distmarker>=1.2.3; platform_system != 'Darwin' or platform_machine != 'arm64'",
    ],
)

EXTRA_REQUIREMENTS = cr.get_requirement_set(
    [
        "dist-extra1<3.0.0,>=2.1.0",
    ],
)

DEV_REQUIREMENTS = cr.get_requirement_set(
    [
        "dist-dev1<2.0.0,>=1.2.3",
    ],
)


def test_pyproject_file__get_requirements(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(PYPROJECT_CONTENTS)

    with cr.PyprojectFile.open(pyproject_path) as pyproject:
        assert pyproject.get_requirements() == MAIN_REQUIREMENTS
        assert pyproject.get_requirements(extra="test_extra") == EXTRA_REQUIREMENTS
        assert pyproject.get_requirements(group="dev") == DEV_REQUIREMENTS


def test_pyproject_file__set_requirements(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[project]
name = "compreq"
version = "0.1.0"
requires-python = "<4,>=3.12"

dependencies = []

[project.optional-dependencies]
test_extra = []

[dependency-groups]
dev = []
""",
    )

    with cr.PyprojectFile.open(pyproject_path) as pyproject:
        compreq = MagicMock(cr.CompReq)
        compreq.context = MagicMock(cr.Context)
        compreq.resolve_requirement_set.side_effect = lambda r: asyncio.run(
            cr.get_lazy_requirement_set(r).resolve(compreq.context),
        )

        pyproject.set_requirements(
            compreq,
            MAIN_REQUIREMENTS,
        )
        pyproject.set_requirements(compreq, EXTRA_REQUIREMENTS, extra="test_extra")
        pyproject.set_requirements(compreq, DEV_REQUIREMENTS, group="dev")

    assert pyproject_path.read_text() == PYPROJECT_CONTENTS_AFTER


def test_pyproject_file__get_requires_python(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[project]
name = "compreq"
version = "0.1.0"
requires-python = "<4,>=3.12"
""",
    )

    with cr.PyprojectFile.open(pyproject_path) as pyproject:
        assert SpecifierSet("<4,>=3.12") == pyproject.get_requires_python()


def test_pyproject_file__set_requires_python(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[project]
name = "compreq"
version = "0.1.0"
requires-python = "<4,>=3.12"
""",
    )

    with cr.PyprojectFile.open(pyproject_path) as pyproject:
        compreq = MagicMock(cr.CompReq)
        compreq.context = MagicMock(cr.Context)

        def fake_resolve_specifier_set(
            distribution: str,
            specifier_set: AnySpecifierSet,
        ) -> SpecifierSet:
            assert distribution == "python"
            return asyncio.run(cr.get_lazy_specifier_set(specifier_set).resolve(compreq.context))

        compreq.resolve_specifier_set.side_effect = fake_resolve_specifier_set

        pyproject.set_requires_python(compreq, "==3.10")

    assert (
        pyproject_path.read_text()
        == """
[project]
name = "compreq"
version = "0.1.0"
requires-python = "==3.10"
"""
    )


def test_pyproject_file__get_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[project]
name = "compreq"
version = "0.1.0"
classifiers = [
    "test1",
    "test2",
    "test3",
]
""",
    )

    with cr.PyprojectFile.open(pyproject_path) as pyproject:
        assert pyproject.get_classifiers() == ["test1", "test2", "test3"]


def test_pyproject_file__set_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[project]
name = "compreq"
version = "0.1.0"
classifiers = [
    "chaff1",
    "chaff2",
]
""",
    )

    with cr.PyprojectFile.open(pyproject_path) as pyproject:
        pyproject.set_classifiers(["test1", "test2", "test3"])

    assert (
        pyproject_path.read_text()
        == """
[project]
name = "compreq"
version = "0.1.0"
classifiers = [
    "test1",
    "test2",
    "test3",
]
"""
    )


def test_pyproject_file__set_python_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[project]
name = "compreq"
version = "0.1.0"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Typing :: Typed",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
""",
    )

    comp_req = MagicMock(cr.CompReq)
    python_releases = fake_release_set(
        distribution="python",
        releases=[
            # NOT sorted:
            "2.6.1",
            "3.1.1",
            "3.0.0",
            "2.7.2",
            "3.0.1",
            "2.7.0",
            "2.7.1",
            "3.1.2",
        ],
    )
    lazy_python_releases = cr.get_lazy_release_set(python_releases)
    comp_req.resolve_release_set.return_value = python_releases

    with cr.PyprojectFile.open(pyproject_path) as pyproject:
        pyproject.set_python_classifiers(comp_req, lazy_python_releases)

    assert (
        pyproject_path.read_text()
        == """
[project]
name = "compreq"
version = "0.1.0"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Typing :: Typed",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.0",
    "Programming Language :: Python :: 3.1",
]
"""
    )
    comp_req.resolve_release_set.assert_called_once_with("python", lazy_python_releases)
