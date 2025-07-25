import asyncio
import datetime as dt

import requests
from dateutil.parser import isoparse
from packaging.version import parse

from compreq.releases import Release, ReleaseSet, infer_and_set_successor
from compreq.time import is_utc_datetime

_cache: dict[str, ReleaseSet] = {}
_cache_lock = asyncio.Lock()


async def get_pypi_releases(distribution: str) -> ReleaseSet:
    """Get all releases of the given distribution, from PyPi."""
    async with _cache_lock:
        release_set = _cache.get(distribution)
        if release_set is not None:
            return release_set

    def _get_releases() -> ReleaseSet:
        url = f"https://pypi.org/pypi/{distribution}/json"
        data = requests.get(url, timeout=600.0).json()
        assert data != {"message": "Not Found"}, distribution
        result = set()
        for version_str, release_data in data["releases"].items():
            version = parse(version_str)
            released_time: dt.datetime | None = None

            for file_data in release_data:
                file_yanked = file_data["yanked"]
                if file_yanked:
                    continue

                file_released_time = isoparse(file_data["upload_time_iso_8601"])
                if released_time is None:
                    released_time = file_released_time
                else:
                    released_time = max(released_time, file_released_time)

            if released_time is None:
                continue

            assert is_utc_datetime(released_time), released_time

            result.add(
                Release(
                    distribution=distribution,
                    version=version,
                    released_time=released_time,
                    successor=None,  # Set by infer_and_set_successor.
                ),
            )
        return infer_and_set_successor(ReleaseSet(distribution, frozenset(result)))

    release_set = await asyncio.to_thread(_get_releases)
    async with _cache_lock:
        _cache[distribution] = release_set
    return release_set
