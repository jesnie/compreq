from pathlib import Path

from compreq import TextReFile


def test_text_re_file(tmp_path: Path) -> None:
    path = tmp_path / "test.txt"
    path.write_text(
        """
foo 123
bar 234
baz 345""",
        encoding="utf-8",
    )

    with TextReFile.open(path) as fp:
        assert fp.sub("test", "test") == 0
        assert fp.sub("23", "xx") == 2
    assert (
        path.read_text(encoding="utf-8")
        == """
foo 1xx
bar xx4
baz 345"""
    )
