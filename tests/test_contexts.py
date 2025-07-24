import datetime as dt

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pytest import MonkeyPatch

from compreq import Context, DefaultContext, ReleaseSet
from tests.utils import fake_release_set, utc


async def test_default_context(monkeypatch: MonkeyPatch) -> None:
    fake_now = utc(dt.datetime(2023, 8, 22, 14, 20))

    python_specifier_ = SpecifierSet("<4.0.0,>=3.9")
    fake_python_releases = fake_release_set(distribution="python", releases=["3.9", "3.10", "3.11"])

    async def fake_get_python_releases(python_specifier: SpecifierSet) -> ReleaseSet:
        assert python_specifier_ == python_specifier
        return fake_python_releases

    monkeypatch.setattr("compreq.contexts.get_python_releases", fake_get_python_releases)

    fake_foobar_releases = fake_release_set(
        distribution="foo.bar",
        releases=["1.2.3", "1.2.4", "1.2.5"],
    )

    async def fake_get_pypi_releases(distribution: str) -> ReleaseSet:
        assert distribution == "foo.bar"
        return fake_foobar_releases

    monkeypatch.setattr("compreq.contexts.get_pypi_releases", fake_get_pypi_releases)

    context = DefaultContext(str(python_specifier_), now=fake_now)
    assert Version("3.9") == context.default_python
    assert python_specifier_ == context.python_specifier
    assert fake_now == context.now
    assert fake_python_releases == await context.releases("python")
    assert fake_foobar_releases == await context.releases("foo.bar")

    dcontext = context.for_distribution("foo.bar")
    assert dcontext.distribution == "foo.bar"
    assert Version("3.9") == dcontext.default_python
    assert python_specifier_ == dcontext.python_specifier
    assert fake_now == dcontext.now
    assert fake_python_releases == await dcontext.releases("python")
    assert fake_foobar_releases == await dcontext.releases("foo.bar")


def test_default_context__for_python(monkeypatch: MonkeyPatch) -> None:
    python_specifier_1 = "<4.0.0,>=3.9"
    default_python_1 = "3.10"
    python_specifier_2 = "<4.0.0,>=3.10"
    default_python_2 = "3.11"

    context: Context

    context = DefaultContext(python_specifier_1, default_python=default_python_1)
    assert Version(default_python_1) == context.default_python
    assert SpecifierSet(python_specifier_1) == context.python_specifier

    context = context.for_python(python_specifier_2, default_python=default_python_2)
    assert Version(default_python_2) == context.default_python
    assert SpecifierSet(python_specifier_2) == context.python_specifier

    context = context.for_python(python_specifier_2)
    assert Version("3.10") == context.default_python
    assert SpecifierSet(python_specifier_2) == context.python_specifier

    context = DefaultContext(python_specifier_1)
    assert Version("3.9") == context.default_python
    assert SpecifierSet(python_specifier_1) == context.python_specifier
