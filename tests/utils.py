from __future__ import annotations

import datetime as dt
from collections.abc import Collection, Mapping
from dataclasses import dataclass

from packaging.version import Version

from compreq import (
    Release,
    ReleaseSet,
    UtcDatetime,
    infer_and_set_successor,
    is_utc_datetime,
)


def utc(time: dt.datetime) -> UtcDatetime:
    if not is_utc_datetime(time):
        time = time.replace(tzinfo=dt.timezone.utc)
    assert is_utc_datetime(time)
    return time


def fake_release(
    *,
    distribution: str = "foo.bar",
    version: str | Version = "1.2.3",
    released_time: dt.datetime = dt.datetime(2023, 8, 11, 12, 49, tzinfo=dt.timezone.utc),
    successor: Release | None = None,
) -> Release:
    if isinstance(version, str):
        version = Version(version)
    assert isinstance(version, Version)
    return Release(distribution, version, utc(released_time), successor)


def fake_release_set(
    *,
    distribution: str = "foo.bar",
    releases: Collection[str | Version | Release] = (),
    infer_successors: bool = True,
) -> ReleaseSet:
    releases_set = set()
    for r in releases:
        if not isinstance(r, Release):
            r = fake_release(distribution=distribution, version=r)
        assert isinstance(r, Release)
        releases_set.add(r)
    release_set = ReleaseSet(distribution, frozenset(releases_set))
    if infer_successors:
        release_set = infer_and_set_successor(release_set)
    return release_set


def assert_release_set(
    expected_distribution: str,
    expected_releases: Collection[tuple[str, UtcDatetime, str | None]],
    actual: ReleaseSet,
) -> None:
    actual_releases: set[tuple[str, UtcDatetime, str | None]] = set()
    assert expected_distribution == actual.distribution
    for r in actual:
        assert expected_distribution == r.distribution
        successor_version = str(r.successor.version) if r.successor else None
        actual_releases.add((str(r.version), r.released_time, successor_version))

    assert set(expected_releases) == actual_releases


@dataclass(frozen=True)
class FakeFtpData:
    modified: UtcDatetime
    children: Mapping[str, FakeFtpData] | None = None
    content: bytes | None = None


def make_fake_ftp_data(files: Collection[tuple[str, UtcDatetime, bytes]]) -> FakeFtpData:
    children = {}
    nest: dict[str, list[tuple[str, UtcDatetime, bytes]]] = {}
    for path, modified, content in files:
        name, _, remaining = path.partition("/")
        assert name, name
        if remaining:
            nest.setdefault(name, []).append((remaining, modified, content))
        else:
            children[name] = FakeFtpData(modified, content=content)
    for child_name, child_files in nest.items():
        children[child_name] = make_fake_ftp_data(child_files)
    return FakeFtpData(
        max(child.modified for child in children.values()),
        children,
    )


@dataclass(frozen=True)
class FakeReply:
    text: str
    content: bytes


def make_fake_reply(content: str | bytes) -> FakeReply:
    if isinstance(content, str):
        return FakeReply(content, content.encode("utf-8"))
    assert isinstance(content, bytes)
    return FakeReply(content.decode("utf-8"), content)


class FakeRequestsGet:
    def __init__(self, data: FakeFtpData, url_prefix: str = "https://www.python.org/ftp/") -> None:
        self._data = data
        self._url_prefix = url_prefix

    def __call__(self, url: str, timeout: float) -> FakeReply:
        assert url.startswith(self._url_prefix)
        url = url[len(self._url_prefix) :].strip("/")
        path = url
        data = self._data
        while url:
            name, _, url = url.partition("/")
            assert data.children
            data = data.children[name]

        if data.children is not None:
            lines = [
                "<html>",
                f"<head><title>Index of /ftp/{path}/</title></head>",
                "<body>",
                f'<h1>Index of /ftp/{path}/</h1><hr><pre><a href="../">../</a>',
            ]
            for name, child in sorted(data.children.items()):
                if child.children is not None:
                    name = name + "/"
                date_str = child.modified.strftime("%d-%b-%Y %H:%M")
                size_str = "-" if child.content is None else str(len(child.content))
                lines.append(
                    f'<a href="{name}">{name}</a>'
                    f"                                               {date_str}"
                    f"                   {size_str}",
                )

            lines.extend(
                [
                    "</pre><hr></body>",
                    "</html>",
                ],
            )

            text = "\n".join(lines)
            return make_fake_reply(text)
        assert data.content is not None
        return make_fake_reply(data.content)
