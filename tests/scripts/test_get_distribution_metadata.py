import json

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pytest import CaptureFixture, MonkeyPatch

from compreq.scripts import get_distribution_metadata


def test_get_distribution_metadata(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["get_distribution_metadata.py", "compreq"])
    get_distribution_metadata.main()
    captured = capsys.readouterr()
    metadata = json.loads(captured.out)
    assert metadata["name"] == "compreq"
    assert Version(metadata["version"])
    assert SpecifierSet(metadata["requires_python"])
    for r in metadata["requires"]:
        assert Requirement(r)
