from collections.abc import Sequence

from compreq.lazy import AnyReleaseSet
from compreq.operators import python_specifier
from compreq.releases import ReleaseSet
from compreq.roots import CompReq


def get_python_classifiers(cr: CompReq, python_releases: AnyReleaseSet | None = None) -> list[str]:
    """Get python distribution classifiers (https://pypi.org/classifiers/) corresponding to the given
    set of python releases.
    """
    version_strs_set = set()
    version_strs_list = []

    def add_version_str(s: str) -> None:
        if s in version_strs_set:
            return
        version_strs_set.add(s)
        version_strs_list.append(s)

    if python_releases is None:
        python_releases = python_specifier()
    assert python_releases is not None
    python_releases = cr.resolve_release_set("python", python_releases)
    assert isinstance(python_releases, ReleaseSet)

    for release in sorted(python_releases):
        v = release.version
        add_version_str(f"{v.major}")
        add_version_str(f"{v.major}.{v.minor}")

    return [f"Programming Language :: Python :: {version_str}" for version_str in version_strs_list]


def set_python_classifiers(
    classifiers: Sequence[str],
    cr: CompReq,
    python_releases: AnyReleaseSet | None = None,
) -> Sequence[str]:
    """Replace python distribution classifiers (https://pypi.org/classifiers/) in `classifiers` with
    those corresponding to `python_releases`.
    """
    classifiers = [c for c in classifiers if not c.startswith("Programming Language :: Python :: ")]
    classifiers += get_python_classifiers(cr, python_releases)
    return classifiers
