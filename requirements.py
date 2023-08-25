from pathlib import Path

import compreq as cr


def set_python_version_in_github_actions(python_release_set: cr.ReleaseSet) -> None:
    minor_versions = sorted(
        set(
            cr.FloorLazyVersion.floor(cr.MINOR, r.version, keep_trailing_zeros=False)
            for r in python_release_set
        )
    )
    default_version = min(minor_versions)
    minor_versions_str = ", ".join(f'"{v}"' for v in minor_versions)
    default_version_str = str(default_version)

    for yaml_path in Path(".github/workflows").glob("*.yml"):
        with cr.TextReFile.open(yaml_path) as ref:
            ref.sub(r"(^ +python-version: \")\d+\.\d+(\")$", rf"\g<1>{default_version_str}\g<2>")
            ref.sub(r"(^ +matrix:\s^ +python: \[).*(\]$)", rf"\g<1>{minor_versions_str}\g<2>")


def set_python_version(
    comp_req: cr.CompReq, pyproject: cr.PoetryPyprojectFile
) -> cr.AnySpecifierSet:
    floor = comp_req.resolve_version(
        "python", cr.floor_ver(cr.MINOR, cr.max_ver(cr.min_age(years=3)))
    )
    ceil = comp_req.resolve_version("python", cr.ceil_ver(cr.MAJOR, cr.max_ver()))
    specfiers = cr.version(">=", floor) & cr.version("<", ceil)

    pyproject.set_python_classifiers(comp_req, specfiers)
    set_python_version_in_github_actions(comp_req.resolve_release_set("python", specfiers))

    tool = pyproject.toml["tool"]
    tool["isort"]["py_version"] = int(f"{floor.major}{floor.minor}")
    tool["black"]["target-version"] = [f"py{floor.major}{floor.minor}"]
    tool["mypy"]["python_version"] = f"{floor.major}.{floor.minor}"

    return specfiers


def main() -> None:
    with cr.PoetryPyprojectFile.open() as pyproject:
        prev_python_specifier = cr.get_bounds(
            pyproject.get_requirements()["python"].specifier
        ).lower_specifier_set()
        comp_req = cr.CompReq(python_specifier=prev_python_specifier)

        python_specifiers = set_python_version(comp_req, pyproject)

        default_range = cr.version(
            ">=",
            cr.floor_ver(
                cr.REL_MINOR,
                cr.minimum_ver(
                    cr.max_ver(cr.min_age(years=1)),
                    cr.min_ver(cr.count(cr.MINOR, 3)),
                ),
            ),
        ) & cr.version("<", cr.ceil_ver(cr.REL_MAJOR, cr.max_ver()))
        dev_range = cr.version(">=", cr.floor_ver(cr.REL_MINOR, cr.max_ver())) & cr.version(
            "<", cr.ceil_ver(cr.REL_MINOR, cr.max_ver())
        )

        pyproject.set_requirements(
            comp_req,
            [
                cr.pkg("beautifulsoup4") & default_range,
                cr.pkg("packaging") & default_range,
                cr.pkg("pip") & default_range,
                cr.pkg("python") & python_specifiers,
                cr.pkg("python-dateutil") & default_range,
                cr.pkg("requests") & default_range,
                cr.pkg("tomlkit") & default_range,
                cr.pkg("typing-extensions") & default_range,
            ],
        )
        pyproject.set_requirements(
            comp_req,
            [
                cr.pkg("black") & dev_range,
                cr.pkg("isort") & dev_range,
                cr.pkg("mypy") & dev_range,
                cr.pkg("pylint") & dev_range,
                cr.pkg("pytest") & dev_range,
                cr.pkg("taskipy") & dev_range,
                cr.pkg("types-beautifulsoup4") & default_range,
                cr.pkg("types-python-dateutil") & default_range,
                cr.pkg("types-requests") & default_range,
            ],
            "dev",
        )

        print(pyproject)


if __name__ == "__main__":
    main()
