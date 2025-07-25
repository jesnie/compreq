import datetime as dt
from typing import Any
from unittest.mock import MagicMock

import pytest

from compreq import get_pypi_releases
from tests.utils import assert_release_set, utc


async def test_pypireleases(monkeypatch: pytest.MonkeyPatch) -> None:
    distribution = "foo.bar"

    def fake_requests_get(url: str, timeout: float) -> Any:
        assert url == f"https://pypi.org/pypi/{distribution}/json"
        reply = MagicMock()
        reply.json.return_value = {
            "releases": {
                "1.2.3": [
                    {
                        "upload_time_iso_8601": "2023-08-23T09:03:00.000000Z",
                        "yanked": False,
                    },
                ],
                "1.2.4a1": [
                    {
                        "upload_time_iso_8601": "2023-08-23T09:04:00.000000Z",
                        "yanked": False,
                    },
                ],
                "1.2.4": [
                    {
                        "upload_time_iso_8601": "2023-08-23T09:05:00.000000Z",
                        "yanked": True,
                    },
                ],
                "1.2.5": [],
                "1.2.6": [
                    {
                        "upload_time_iso_8601": "2023-08-23T09:06:00.000000Z",
                        "yanked": False,
                    },
                    {
                        "upload_time_iso_8601": "2023-08-23T09:07:00.000000Z",
                        "yanked": False,
                    },
                ],
            },
        }
        return reply

    monkeypatch.setattr("compreq.pythonftp.requests.get", fake_requests_get)

    assert_release_set(
        distribution,
        [
            ("1.2.3", utc(dt.datetime(2023, 8, 23, 9, 3)), "1.2.6"),
            ("1.2.4a1", utc(dt.datetime(2023, 8, 23, 9, 4)), "1.2.6"),
            ("1.2.6", utc(dt.datetime(2023, 8, 23, 9, 7)), None),
        ],
        await get_pypi_releases(distribution),
    )
