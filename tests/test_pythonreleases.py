import datetime as dt

from packaging.specifiers import SpecifierSet
from pytest import MonkeyPatch

from compreq import get_python_releases
from tests.utils import FakeRequestsGet, assert_release_set, make_fake_ftp_data, utc


async def test_pythonreleases(monkeypatch: MonkeyPatch) -> None:
    fake_requests_get = FakeRequestsGet(
        make_fake_ftp_data(
            [
                (
                    "python/2.6.1/Python-2.6.1.tgz",
                    utc(dt.datetime(2023, 8, 22, 16, 0)),
                    b"Version 2.6.1 binary",
                ),
                (
                    "python/2.7.9/Python-2.7.9.tgz",
                    utc(dt.datetime(2023, 8, 22, 16, 1)),
                    b"Version 2.7.9 binary",
                ),
                ("python/2.7.10/Python-2.7.10.zip", utc(dt.datetime(2023, 8, 22, 16, 2)), b"chaff"),
                (
                    "python/chaff/Python-2.7.11.tgz",
                    utc(dt.datetime(2023, 8, 22, 16, 3)),
                    b"chaff",
                ),
                ("python/Python-2.7.12.tgz", utc(dt.datetime(2023, 8, 22, 16, 4)), b"chaff"),
                (
                    "python/3.9.0/Python-3.9.0a1.tgz",
                    utc(dt.datetime(2023, 8, 22, 16, 5)),
                    b"Version 3.9.0a1 binary",
                ),
                (
                    "python/3.9.0/Python-3.9.0.tgz",
                    utc(dt.datetime(2023, 8, 22, 16, 6)),
                    b"Version 3.9.0 binary",
                ),
                (
                    "python/3.9.1/Python-3.9.1.tgz",
                    utc(dt.datetime(2023, 8, 22, 16, 7)),
                    b"Version 3.9.1 binary",
                ),
            ],
        ),
    )

    monkeypatch.setattr("compreq.pythonftp.requests.get", fake_requests_get)

    assert_release_set(
        "python",
        [
            ("2.7.9", utc(dt.datetime(2023, 8, 22, 16, 1)), "3.9.0"),
            ("3.9.0a1", utc(dt.datetime(2023, 8, 22, 16, 5)), "3.9.0"),
            ("3.9.0", utc(dt.datetime(2023, 8, 22, 16, 6)), "3.9.1"),
            ("3.9.1", utc(dt.datetime(2023, 8, 22, 16, 7)), None),
        ],
        await get_python_releases(SpecifierSet(">=2.7")),
    )
