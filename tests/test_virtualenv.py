import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from packaging.requirements import Requirement
from packaging.version import Version
from pytest import MonkeyPatch

import compreq as cr
from compreq.scripts import get_distribution_metadata


@pytest.fixture(autouse=True)
def mock_run(monkeypatch: MonkeyPatch) -> MagicMock:
    mock_run = MagicMock()

    async def _create_subprocess_shell(*args: Any, **kwargs: Any) -> Any:
        return mock_run.proc

    mock_run.side_effect = _create_subprocess_shell

    monkeypatch.setattr("compreq.virtualenv.asyncio.create_subprocess_shell", mock_run)

    async def _communicate() -> tuple[bytes | None, bytes | None]:
        return mock_run.stdout_bytes, mock_run.stderr_bytes

    mock_run.proc = MagicMock(returncode=0, communicate=_communicate)

    return mock_run


async def test_create_venv(mock_run: MagicMock) -> None:
    await cr.create_venv("/home/jesper/venv", "3.10.1")
    mock_run.assert_called_once_with(
        "virtualenv -p python3.10 /home/jesper/venv",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )


async def test_remove_venv(tmp_path: Path) -> None:
    venv_path = tmp_path / "venv"
    venv_path.mkdir()
    (venv_path / "test.txt").touch()
    assert venv_path.exists()

    venv = cr.VirtualEnv(venv_path)

    await cr.remove_venv(venv)

    assert not venv_path.exists()
    assert tmp_path.is_dir()


async def test_temp_venv(mock_run: MagicMock) -> None:
    async with cr.temp_venv("3.10") as venv:
        path = venv._path
        assert path.exists()
        mock_run.assert_called_once_with(
            f"virtualenv -p python3.10 {path}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    assert not path.exists()

    mock_run.reset_mock()

    with pytest.raises(ValueError):  # noqa: PT012
        async with cr.temp_venv("3.10") as venv:
            path = venv._path
            assert path.exists()
            mock_run.assert_called_once_with(
                f"virtualenv -p python3.10 {path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            raise ValueError("test error")
    assert not path.exists()


async def test_temp_venv__no_clean_on_error(mock_run: MagicMock) -> None:
    async with cr.temp_venv("3.10", clean_on_error=False) as venv:
        path = venv._path
        assert path.exists()
        mock_run.assert_called_once_with(
            f"virtualenv -p python3.10 {path}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    assert not path.exists()

    mock_run.reset_mock()

    with pytest.raises(ValueError):  # noqa: PT012
        async with cr.temp_venv("3.10", clean_on_error=False) as venv:
            path = venv._path
            assert path.exists()
            mock_run.assert_called_once_with(
                f"virtualenv -p python3.10 {path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            raise ValueError("test error")
    assert path.exists()


async def test_virtual_env__run(mock_run: MagicMock) -> None:
    mock_run.stdout_bytes = b"Hello, world!"
    venv = cr.VirtualEnv("/home/jesper/venv")

    assert await venv.run("foo bar baz") == "Hello, world!"

    mock_run.assert_called_once_with(
        ". /home/jesper/venv/bin/activate && foo bar baz",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )


async def test_virtual_env__install(mock_run: MagicMock) -> None:
    venv = cr.VirtualEnv("/home/jesper/venv")

    await venv.install(
        cr.get_requirement_set(
            [
                Requirement("foo>=1.2.3"),
                Requirement("bar<2.0,>=1.0"),
            ],
        ),
    )

    mock_run.assert_called_once_with(
        '. /home/jesper/venv/bin/activate && pip install "bar<2.0,>=1.0" "foo>=1.2.3"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )


async def test_virtual_env__install__no_deps(mock_run: MagicMock) -> None:
    venv = cr.VirtualEnv("/home/jesper/venv")

    await venv.install(
        cr.get_requirement_set(
            [
                Requirement("foo>=1.2.3"),
                Requirement("bar<2.0,>=1.0"),
            ],
        ),
        deps=False,
    )

    mock_run.assert_called_once_with(
        '. /home/jesper/venv/bin/activate && pip install --no-deps "bar<2.0,>=1.0" "foo>=1.2.3"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )


async def test_virtual_env__distribution_metadata(mock_run: MagicMock) -> None:
    mock_run.stdout_bytes = b"""{
  "name": "foo.bar",
  "version": "1.2.3",
  "requires_python": "<4.0,>=3.9",
  "requires": [
    "foo>=1.2.3",
    "bar<2.0,>=1.0"
  ]
}
"""

    venv = cr.VirtualEnv("/home/jesper/venv")
    assert cr.DistributionMetadata(
        distribution="foo.bar",
        version=Version("1.2.3"),
        requires=cr.get_requirement_set(
            [
                Requirement("python<4.0,>=3.9"),
                Requirement("foo>=1.2.3"),
                Requirement("bar<2.0,>=1.0"),
            ],
        ),
    ) == await venv.distribution_metadata("foo.bar")
    mock_run.assert_called_once_with(
        f". /home/jesper/venv/bin/activate && python {get_distribution_metadata.__file__} foo.bar",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
