import datetime as dt

import pytest

from compreq import PYTHON_FTP_ROOT
from tests.utils import FakeRequestsGet, make_fake_ftp_data, utc


def test_pythonftp(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_requests_get = FakeRequestsGet(
        make_fake_ftp_data(
            [
                ("a/a1.txt", utc(dt.datetime(2023, 8, 22, 15, 1)), b"a1 contents"),
                ("a/a2.txt", utc(dt.datetime(2023, 8, 22, 15, 2)), b"a2 contents"),
                ("b.txt", utc(dt.datetime(2023, 8, 22, 15, 3)), b"b contents"),
            ],
        ),
    )

    monkeypatch.setattr("compreq.pythonftp.requests.get", fake_requests_get)

    root_ls = PYTHON_FTP_ROOT.ls()
    assert {"a/", "b.txt"} == set(root_ls)

    a = root_ls["a/"].as_dir()
    assert a.path_str == "/a/"
    assert utc(dt.datetime(2023, 8, 22, 15, 2)) == a.modified
    assert a.url == "https://www.python.org/ftp/a/"
    with pytest.raises(AssertionError):
        a.as_file()
    a_ls = a.ls()
    assert {"a1.txt", "a2.txt"} == set(a_ls)

    a1 = a_ls["a1.txt"].as_file()
    assert a1.path_str == "/a/a1.txt"
    assert utc(dt.datetime(2023, 8, 22, 15, 1)) == a1.modified
    assert a1.url == "https://www.python.org/ftp/a/a1.txt"
    with pytest.raises(AssertionError):
        a1.as_dir()
    assert a1.read_text() == "a1 contents"
    assert a1.read_bytes() == b"a1 contents"

    a2 = a_ls["a2.txt"].as_file()
    assert a2.path_str == "/a/a2.txt"
    assert utc(dt.datetime(2023, 8, 22, 15, 2)) == a2.modified
    assert a2.url == "https://www.python.org/ftp/a/a2.txt"
    with pytest.raises(AssertionError):
        a2.as_dir()
    assert a2.read_text() == "a2 contents"
    assert a2.read_bytes() == b"a2 contents"

    b = root_ls["b.txt"].as_file()
    assert b.path_str == "/b.txt"
    assert utc(dt.datetime(2023, 8, 22, 15, 3)) == b.modified
    assert b.url == "https://www.python.org/ftp/b.txt"
    with pytest.raises(AssertionError):
        b.as_dir()
    assert b.read_text() == "b contents"
    assert b.read_bytes() == b"b contents"
