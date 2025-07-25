# Examples:
# argon2-cffi = {extras = ["argon2"], version = "^23.1.0"}
# pip = {git = "https://github.com/pypa/pip"}
# beautifulsoup = {url = "http://www.crummy.com/software/BeautifulSoup/unreleased/4.x/BeautifulSoup-4.0b.tar.gz"}
# tensorflow = {version = ">=2.8.0", markers = "platform_system != \"Darwin\" or platform_machine != \"arm64\""}
# check-shapes = {path = "/home/foo/src/check_shapes"}

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

from packaging.requirements import Requirement

import compreq as cr
from tests.utils import fake_release_set

PYPROJECT_CONTENTS = """
[tool.poetry]
name = "compreq"
version = "0.1.0"

[tool.poetry.dependencies]
dist1 = "!=1.2.5,<2.0.0,>=1.2.3"
dist2 = "<=1.9.0,>1.2.3"
dist3 = "1.2.5"
dist4 = "~1.2"
dist5 = "^1.2.3"
dist6 = "^0.1.0"
distextra = {extras = ["extra1", "extra2"], version = "^1.2.3"}
distgit = {git = "https://github.com/dist6/dist6"}
distmarker = {version = ">=1.2.3", markers = "platform_system != \\"Darwin\\" or platform_machine != 'arm64'"}
distoptional = {optional = true, version = ">=1.2.3"}
distpath = {path = "/home/compreq"}
disturl = {url = "http://www.test.com/test/dist7-1.2.3.tar.gz"}

[tool.poetry.group.dev.dependencies]
dist-dev1 = "<2.0.0,>=1.2.3"
"""

PYPROJECT_CONTENTS_AFTER = """
[tool.poetry]
name = "compreq"
version = "0.1.0"

[tool.poetry.dependencies]
dist1 = "!=1.2.5,<2.0.0,>=1.2.3"
dist2 = "<=1.9.0,>1.2.3"
dist3 = "1.2.5"
dist4 = "~1.2"
dist5 = "<2.0.0,>=1.2.3"
dist6 = "<0.2.0,>=0.1.0"
distextra = {extras = ["extra1", "extra2"], version = "<2.0.0,>=1.2.3"}
distgit = {git = "https://github.com/dist6/dist6"}
distmarker = {version = ">=1.2.3", markers = "platform_system != \\"Darwin\\" or platform_machine != \\"arm64\\""}
distoptional = {version = ">=1.2.3", optional = true}
distpath = {path = "/home/compreq"}
disturl = {url = "http://www.test.com/test/dist7-1.2.3.tar.gz"}

[tool.poetry.group.dev.dependencies]
dist-dev1 = "<2.0.0,>=1.2.3"
"""

MAIN_REQUIREMENTS = cr.get_requirement_set(
    [
        "dist1!=1.2.5,<2.0.0,>=1.2.3",
        "dist2<=1.9.0,>1.2.3",
        "dist3==1.2.5",
        "dist4~=1.2",
        "dist5<2.0.0,>=1.2.3",
        "dist6<0.2.0,>=0.1.0",
        "distextra[extra1, extra2]<2.0.0,>=1.2.3",
        "disturl@http://www.test.com/test/dist7-1.2.3.tar.gz",
        "distpath@file:///home/compreq",
        "distgit@git+https://github.com/dist6/dist6",
        "distmarker>=1.2.3; platform_system != 'Darwin' or platform_machine != 'arm64'",
        cr.OptionalRequirement(Requirement("distoptional>=1.2.3"), optional=True),
    ],
)

DEV_REQUIREMENTS = cr.get_requirement_set(
    [
        "dist-dev1<2.0.0,>=1.2.3",
    ],
)


def test_poetry_pyproject_file__get_requirements(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(PYPROJECT_CONTENTS)

    with cr.PoetryPyprojectFile.open(pyproject_path) as pyproject:
        assert pyproject.get_requirements() == MAIN_REQUIREMENTS
        assert pyproject.get_requirements(group="dev") == DEV_REQUIREMENTS


def test_poetry_pyproject_file__set_requirements(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"

[tool.poetry.dependencies]

[tool.poetry.group.dev.dependencies]
""",
    )

    with cr.PoetryPyprojectFile.open(pyproject_path) as pyproject:
        compreq = MagicMock(cr.CompReq)
        compreq.context = MagicMock(cr.Context)
        compreq.resolve_requirement_set.side_effect = lambda r: asyncio.run(
            cr.get_lazy_requirement_set(r).resolve(compreq.context),
        )

        pyproject.set_requirements(
            compreq,
            MAIN_REQUIREMENTS,
        )
        pyproject.set_requirements(compreq, DEV_REQUIREMENTS, group="dev")

    assert pyproject_path.read_text() == PYPROJECT_CONTENTS_AFTER


def test_poetry_pyproject_file__get_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"
classifiers = [
    "test1",
    "test2",
    "test3",
]
""",
    )

    with cr.PoetryPyprojectFile.open(pyproject_path) as pyproject:
        assert pyproject.get_classifiers() == ["test1", "test2", "test3"]


def test_poetry_pyproject_file__set_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"
classifiers = [
    "chaff1",
    "chaff2",
]
""",
    )

    with cr.PoetryPyprojectFile.open(pyproject_path) as pyproject:
        pyproject.set_classifiers(["test1", "test2", "test3"])

    assert (
        pyproject_path.read_text()
        == """
[tool.poetry]
name = "compreq"
version = "0.1.0"
classifiers = [
    "test1",
    "test2",
    "test3",
]
"""
    )


def test_poetry_pyproject_file__set_python_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[tool.poetry]
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

    with cr.PoetryPyprojectFile.open(pyproject_path) as pyproject:
        pyproject.set_python_classifiers(comp_req, lazy_python_releases)

    assert (
        pyproject_path.read_text()
        == """
[tool.poetry]
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
