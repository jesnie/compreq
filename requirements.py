import re
from typing import Any, Collection, Sequence

from packaging.specifiers import SpecifierSet
from tomlkit import dump, dumps, load

import compreq.factory as f
import compreq.operators as o
from compreq.context import DefaultContext
from compreq.lazy import AnyRequirement, AnySpecifierSet
from compreq.root import CompReq

# TODO(jesper): Support natively:
MONTH_DAYS = 30
YEAR_DAYS = 365


def get_python_specifier(pyproject: Any) -> SpecifierSet:
    prev_python = pyproject["tool"]["poetry"]["dependencies"]["python"]
    match = re.fullmatch("<4.0.0,(>=.*)", prev_python)
    assert match
    return SpecifierSet(match[1])


def get_python_classifiers(cr: CompReq, python_specifiers: AnySpecifierSet) -> list[str]:
    version_strs_set = set()
    version_strs_list = []

    def add_version_str(s: str) -> None:
        if s in version_strs_set:
            return
        version_strs_set.add(s)
        version_strs_list.append(s)

    for release in sorted(cr.resolve_release_set("python", python_specifiers).releases):
        v = release.version
        add_version_str(f"{v.major}")
        add_version_str(f"{v.major}.{v.minor}")

    return [f"Programming Language :: Python :: {version_str}" for version_str in version_strs_list]


def set_python_classifiers(
    classifiers: Sequence[str], cr: CompReq, python_specifiers: AnySpecifierSet
) -> Sequence[str]:
    classifiers = [c for c in classifiers if not c.startswith("Programming Language :: Python :: ")]
    classifiers += get_python_classifiers(cr, python_specifiers)
    return classifiers


def set_python_version(cr: CompReq, pyproject: Any) -> AnySpecifierSet:
    floor = cr.resolve_version(
        "python", o.floor_ver(o.MINOR, o.max_ver(o.min_age(days=3 * YEAR_DAYS)))
    )
    ceil = cr.resolve_version("python", o.ceil_ver(o.MAJOR, o.max_ver()))
    specfiers = f.version(">=", floor) & f.version("<", ceil)

    tool = pyproject["tool"]
    poetry = tool["poetry"]
    poetry["classifiers"] = set_python_classifiers(poetry["classifiers"], cr, specfiers)
    poetry["classifiers"].multiline(True)

    tool["isort"]["py_version"] = int(f"{floor.major}{floor.minor}")
    tool["black"]["target-version"] = [f"py{floor.major}{floor.minor}"]
    tool["mypy"]["python_version"] = f"{floor.major}.{floor.minor}"

    return specfiers


def set_dependencies(
    cr: CompReq, pyproject: Any, group: str | None, requirements: Collection[AnyRequirement]
) -> None:
    dependencies: dict[str, str] = {}
    rs = [cr.resolve_requirement(r) for r in requirements]
    for r in sorted(rs, key=lambda r: r.name):
        assert r.url is None, f"TODO {r.url}"
        assert not r.extras, f"TODO {r.extras}"
        assert r.marker is None, f"TODO {r.marker}"
        dependencies[r.name] = str(r.specifier)
    poetry = pyproject["tool"]["poetry"]

    if group is None:
        target = poetry["dependencies"]
    else:
        target = poetry["group"][group]["dependencies"]
    target.clear()
    target.update(dependencies)


def main() -> None:
    with open("pyproject.toml", "rt", encoding="utf-8") as inf:
        pyproject: Any = load(inf)

    ctx = DefaultContext(get_python_specifier(pyproject))
    cr = CompReq(ctx)

    python_specifiers = set_python_version(cr, pyproject)

    default_range = f.version(
        ">=", o.floor_ver(o.MINOR, o.max_ver(o.min_age(days=YEAR_DAYS)))
    ) & f.version("<", o.ceil_ver(o.MAJOR, o.max_ver()))
    dev_range = f.version(">=", o.floor_ver(o.MINOR, o.max_ver())) & f.version(
        "<", o.ceil_ver(o.MINOR, o.max_ver())
    )

    set_dependencies(
        cr,
        pyproject,
        None,
        [
            f.pkg("beautifulsoup4") & default_range,
            f.pkg("packaging") & default_range,
            f.pkg("pip") & default_range,
            f.pkg("python") & python_specifiers,
            f.pkg("python-dateutil") & default_range,
            f.pkg("requests") & default_range,
        ],
    )

    set_dependencies(
        cr,
        pyproject,
        "dev",
        [
            f.pkg("black") & dev_range,
            f.pkg("isort") & dev_range,
            f.pkg("mypy") & dev_range,
            f.pkg("pylint") & dev_range,
            f.pkg("pytest") & dev_range,
            f.pkg("taskipy") & dev_range,
            f.pkg("tomlkit") & dev_range,
            f.pkg("types-beautifulsoup4") & default_range,
            f.pkg("types-python-dateutil") & default_range,
            f.pkg("types-requests") & default_range,
        ],
    )

    print(dumps(pyproject))
    with open("pyproject.toml", "wt", encoding="utf-8") as outf:
        dump(pyproject, outf)


if __name__ == "__main__":
    main()