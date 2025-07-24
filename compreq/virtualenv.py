import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from compreq.levels import MINOR
from compreq.paths import AnyPath
from compreq.requirements import RequirementSet, get_requirement_set, make_requirement
from compreq.rounding import floor
from compreq.scripts import get_distribution_metadata


async def _run(command: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout_bytes, _ = await proc.communicate()
    stdout = stdout_bytes.decode("utf-8")
    assert proc.returncode == 0, (command, stdout)
    return stdout


@dataclass
class DistributionMetadata:
    distribution: str
    version: Version
    requires: RequirementSet


class VirtualEnv:
    def __init__(self, path: AnyPath) -> None:
        self._path = Path(path)

    async def run(self, command: str) -> str:
        return await _run(f". {self._path}/bin/activate && {command}")

    async def install(self, requirement_set: RequirementSet, deps: bool = True) -> None:
        tokens = ["pip install"]
        if not deps:
            tokens.append("--no-deps")
        tokens.extend(f'"{r.requirement}"' for r in requirement_set.values())
        await self.run(" ".join(tokens))

    async def distribution_metadata(self, distribution: str) -> DistributionMetadata:
        output = await self.run(f"python {get_distribution_metadata.__file__} {distribution}")
        data = json.loads(output)
        version = Version(data["version"])
        python_requires = make_requirement(
            distribution="python",
            specifier=SpecifierSet(data["requires_python"]),
        )
        requires = [python_requires] + [Requirement(r) for r in data["requires"]]
        return DistributionMetadata(
            distribution=distribution,
            version=version,
            requires=get_requirement_set(requires),
        )


async def create_venv(path: AnyPath, python_version: str | Version) -> VirtualEnv:
    if isinstance(python_version, str):
        python_version = Version(python_version)
    assert isinstance(python_version, Version)
    python_version = floor(MINOR, python_version, keep_trailing_zeros=False)
    path_ = Path(path)
    await _run(f"virtualenv -p python{python_version} {path_}")
    return VirtualEnv(path_)


async def remove_venv(venv: VirtualEnv) -> None:
    await asyncio.to_thread(rmtree, venv._path)
    venv._path = None  # type: ignore[assignment]


@asynccontextmanager
async def temp_venv(
    python_version: str | Version,
    clean_on_error: bool = True,
) -> AsyncIterator[VirtualEnv]:
    path = mkdtemp("compreq_venv")
    venv = await create_venv(path, python_version)
    if clean_on_error:
        try:
            yield venv
        finally:
            await remove_venv(venv)
    else:
        yield venv
        await remove_venv(venv)
