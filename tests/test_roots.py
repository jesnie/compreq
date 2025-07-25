from unittest.mock import MagicMock

from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from compreq import (
    CompReq,
    Context,
    DistributionContext,
    LazyRelease,
    LazyReleaseSet,
    LazyRequirement,
    LazyRequirementSet,
    LazySpecifier,
    LazySpecifierSet,
    LazyVersion,
    get_requirement_set,
)
from tests.utils import fake_release, fake_release_set


def test_comp_req__for_python() -> None:
    context_1 = MagicMock(Context)
    context_2 = MagicMock(Context)
    context_1.for_python.return_value = context_2

    cr = CompReq(context=context_1)

    cr = cr.for_python("<4.0,>=3.9")

    assert context_2 == cr._context
    context_1.for_python.assert_called_once_with(python_specifier="<4.0,>=3.9", default_python=None)


def test_comp_req__resolve_release() -> None:
    context = MagicMock(Context)
    dcontext = MagicMock(DistributionContext)
    context.for_distribution.return_value = dcontext

    release = fake_release(distribution="foo.bar", version="1.2.3")
    lazy = MagicMock(LazyRelease)
    lazy.resolve.return_value = release

    cr = CompReq(context=context)

    assert release == cr.resolve_release("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(dcontext)
    context.for_distribution.assert_called_once_with("foo.bar")


def test_comp_req__resolve_release_set() -> None:
    context = MagicMock(Context)
    dcontext = MagicMock(DistributionContext)
    context.for_distribution.return_value = dcontext

    release_set = fake_release_set(distribution="foo.bar", releases=["1.2.3", "1.2.4", "1.2.5"])
    lazy = MagicMock(LazyReleaseSet)
    lazy.resolve.return_value = release_set

    cr = CompReq(context=context)

    assert release_set == cr.resolve_release_set("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(dcontext)
    context.for_distribution.assert_called_once_with("foo.bar")


def test_comp_req__resolve_version() -> None:
    context = MagicMock(Context)
    dcontext = MagicMock(DistributionContext)
    context.for_distribution.return_value = dcontext

    version = Version("1.2.3")
    lazy = MagicMock(LazyVersion)
    lazy.resolve.return_value = version

    cr = CompReq(context=context)

    assert version == cr.resolve_version("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(dcontext)
    context.for_distribution.assert_called_once_with("foo.bar")


def test_comp_req__resolve_specifier() -> None:
    context = MagicMock(Context)
    dcontext = MagicMock(DistributionContext)
    context.for_distribution.return_value = dcontext

    specifier = Specifier("~=1.2.3")
    lazy = MagicMock(LazySpecifier)
    lazy.resolve.return_value = specifier

    cr = CompReq(context=context)

    assert specifier == cr.resolve_specifier("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(dcontext)
    context.for_distribution.assert_called_once_with("foo.bar")


def test_comp_req__resolve_specifier_set() -> None:
    context = MagicMock(Context)
    dcontext = MagicMock(DistributionContext)
    context.for_distribution.return_value = dcontext

    specifier_set = SpecifierSet("<2.0.0,>=1.2.3")
    lazy = MagicMock(LazySpecifierSet)
    lazy.resolve.return_value = specifier_set

    cr = CompReq(context=context)

    assert specifier_set == cr.resolve_specifier_set("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(dcontext)
    context.for_distribution.assert_called_once_with("foo.bar")


def test_comp_req__resolve_requirement() -> None:
    context = MagicMock(Context)

    requirement = Requirement("foo.bar~=1.2.3")
    lazy = MagicMock(LazyRequirement)
    lazy.resolve.return_value = requirement

    cr = CompReq(context=context)

    assert requirement == cr.resolve_requirement(lazy)
    lazy.resolve.assert_called_once_with(context)


def test_comp_req__resolve_requirement_set() -> None:
    context = MagicMock(Context)

    requirement_set = get_requirement_set(
        [Requirement("foo.bar~=1.2.3"), Requirement("baz==2.0.0")],
    )
    lazy = MagicMock(LazyRequirementSet)
    lazy.resolve.return_value = requirement_set

    cr = CompReq(context=context)

    assert requirement_set == cr.resolve_requirement_set(lazy)
    lazy.resolve.assert_called_once_with(context)
