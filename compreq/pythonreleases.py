import asyncio
import re
from itertools import chain

from packaging.specifiers import SpecifierSet
from packaging.version import VERSION_PATTERN, Version, parse

from compreq.pythonftp import ROOT, FtpDir
from compreq.releases import Release, ReleaseSet, infer_and_set_successor

RELEASE_DIR_RE = re.compile(r"(" + VERSION_PATTERN + r")/", re.VERBOSE | re.IGNORECASE)
VERSION_TGZ_RE = re.compile(r"Python-(" + VERSION_PATTERN + r").tgz", re.VERBOSE | re.IGNORECASE)


_cache: dict[SpecifierSet, ReleaseSet] = {}
_cache_lock = asyncio.Lock()


async def get_python_releases(python_specifiers: SpecifierSet) -> ReleaseSet:
    """Get all releases of Python.

    The `python_specifiers` argument is used to pre-filter the Python versions to fetch. This
    function can be a bit slow, and setting a tight pre-filter can significantly speed it up. If you
    *really* want to fetch *all* Python releases use `get_python_releases(SpecifierSet())`.
    """
    async with _cache_lock:
        release_set = _cache.get(python_specifiers)
        if release_set is not None:
            return release_set

    assert not any(
        Version(s.version).is_prerelease or Version(s.version).is_devrelease
        for s in python_specifiers
    ), (
        "Initial Python filter specifiers do not supper pre- or dev releases."
        f" Found: {python_specifiers}."
    )

    python = ROOT.ls()["python/"].as_dir()

    def _get_releases(release_dir: FtpDir) -> set[Release]:
        return {
            Release(
                distribution="python",
                version=parse(match[1]),
                released_time=path.modified,
                successor=None,  # Set by infer_and_set_successor
            )
            for name, path in release_dir.ls().items()
            if (match := VERSION_TGZ_RE.fullmatch(name))
        }

    tasks = []
    for release, release_dir in python.ls().items():
        match = RELEASE_DIR_RE.fullmatch(release)
        if match is None:
            continue

        version = parse(match[1])
        if version not in python_specifiers:
            continue

        tasks.append(asyncio.to_thread(_get_releases, release_dir.as_dir()))

    releases = frozenset(chain.from_iterable(await asyncio.gather(*tasks)))
    release_set = infer_and_set_successor(ReleaseSet("python", releases))
    async with _cache_lock:
        _cache[python_specifiers] = release_set
    return release_set
