from typing import Any

import pytest
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from compreq import Bounds, get_bounds


def specifier_set_id(key: Any) -> str | None:
    if isinstance(key, SpecifierSet):
        return str(key)
    return None


@pytest.mark.parametrize(
    "specifier_set,expected",
    [
        (SpecifierSet(), Bounds(SpecifierSet(), None, False, None, False, set())),
        (
            SpecifierSet(">1.2.3"),
            Bounds(SpecifierSet(">1.2.3"), None, False, Version("1.2.3"), False, set()),
        ),
        (
            SpecifierSet(">=1.2.3"),
            Bounds(SpecifierSet(">=1.2.3"), None, False, Version("1.2.3"), True, set()),
        ),
        (
            SpecifierSet("<1.2.3"),
            Bounds(SpecifierSet("<1.2.3"), Version("1.2.3"), False, None, False, set()),
        ),
        (
            SpecifierSet("<=1.2.3"),
            Bounds(SpecifierSet("<=1.2.3"), Version("1.2.3"), True, None, False, set()),
        ),
        (
            SpecifierSet("~=1.2.3"),
            Bounds(SpecifierSet("~=1.2.3"), Version("1.2.4"), False, Version("1.2.3"), True, set()),
        ),
        (
            SpecifierSet("==1.2.3"),
            Bounds(SpecifierSet("==1.2.3"), Version("1.2.3"), True, Version("1.2.3"), True, set()),
        ),
        (
            SpecifierSet("!=1.2.3"),
            Bounds(SpecifierSet("!=1.2.3"), None, False, None, False, {Version("1.2.3")}),
        ),
        (
            SpecifierSet(">2.0.0,>1.2.3"),
            Bounds(SpecifierSet(">2.0.0,>1.2.3"), None, False, Version("2.0.0"), False, set()),
        ),
        (
            SpecifierSet(">2.0.0,>=1.2.3"),
            Bounds(SpecifierSet(">2.0.0,>=1.2.3"), None, False, Version("2.0.0"), False, set()),
        ),
        (
            SpecifierSet(">2.0.0,<1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">2.0.0,<=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">2.0.0,~=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">2.0.0,==1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">2.0.0,!=1.2.3"),
            Bounds(SpecifierSet(">2.0.0,!=1.2.3"), None, False, Version("2.0.0"), False, set()),
        ),
        (
            SpecifierSet(">=2.0.0,>1.2.3"),
            Bounds(SpecifierSet(">=2.0.0,>1.2.3"), None, False, Version("2.0.0"), True, set()),
        ),
        (
            SpecifierSet(">=2.0.0,>=1.2.3"),
            Bounds(SpecifierSet(">=2.0.0,>=1.2.3"), None, False, Version("2.0.0"), True, set()),
        ),
        (
            SpecifierSet(">=2.0.0,<1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">=2.0.0,<=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">=2.0.0,~=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">=2.0.0,==1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">=2.0.0,!=1.2.3"),
            Bounds(SpecifierSet(">=2.0.0,!=1.2.3"), None, False, Version("2.0.0"), True, set()),
        ),
        (
            SpecifierSet("<2.0.0,>1.2.3"),
            Bounds(
                SpecifierSet("<2.0.0,>1.2.3"),
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("<2.0.0,>=1.2.3"),
            Bounds(
                SpecifierSet("<2.0.0,>=1.2.3"),
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<2.0.0,<1.2.3"),
            Bounds(
                SpecifierSet("<2.0.0,<1.2.3"),
                Version("1.2.3"),
                False,
                None,
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("<2.0.0,<=1.2.3"),
            Bounds(SpecifierSet("<2.0.0,<=1.2.3"), Version("1.2.3"), True, None, False, set()),
        ),
        (
            SpecifierSet("<2.0.0,~=1.2.3"),
            Bounds(
                SpecifierSet("<2.0.0,~=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<2.0.0,==1.2.3"),
            Bounds(
                SpecifierSet("<2.0.0,==1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<2.0.0,!=1.2.3"),
            Bounds(
                SpecifierSet("<2.0.0,!=1.2.3"),
                Version("2.0.0"),
                False,
                None,
                False,
                {Version("1.2.3")},
            ),
        ),
        (
            SpecifierSet("<=2.0.0,>1.2.3"),
            Bounds(
                SpecifierSet("<=2.0.0,>1.2.3"),
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("<=2.0.0,>=1.2.3"),
            Bounds(
                SpecifierSet("<=2.0.0,>=1.2.3"),
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<=2.0.0,<1.2.3"),
            Bounds(SpecifierSet("<=2.0.0,<1.2.3"), Version("1.2.3"), False, None, False, set()),
        ),
        (
            SpecifierSet("<=2.0.0,<=1.2.3"),
            Bounds(SpecifierSet("<=2.0.0,<=1.2.3"), Version("1.2.3"), True, None, False, set()),
        ),
        (
            SpecifierSet("<=2.0.0,~=1.2.3"),
            Bounds(
                SpecifierSet("<=2.0.0,~=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<=2.0.0,==1.2.3"),
            Bounds(
                SpecifierSet("<=2.0.0,==1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<=2.0.0,!=1.2.3"),
            Bounds(
                SpecifierSet("<=2.0.0,!=1.2.3"),
                Version("2.0.0"),
                True,
                None,
                False,
                {Version("1.2.3")},
            ),
        ),
        (
            SpecifierSet("~=2.0.0,>1.2.3"),
            Bounds(
                SpecifierSet("~=2.0.0,>1.2.3"),
                Version("2.0.1"),
                False,
                Version("2.0.0"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("~=2.0.0,>=1.2.3"),
            Bounds(
                SpecifierSet("~=2.0.0,>=1.2.3"),
                Version("2.0.1"),
                False,
                Version("2.0.0"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("~=2.0.0,<1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("~=2.0.0,<=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("~=2.0.0,~=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("~=2.0.0,==1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("~=2.0.0,!=1.2.3"),
            Bounds(
                SpecifierSet("~=2.0.0,!=1.2.3"),
                Version("2.0.1"),
                False,
                Version("2.0.0"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("==2.0.0,>1.2.3"),
            Bounds(
                SpecifierSet("==2.0.0,>1.2.3"),
                Version("2.0.0"),
                True,
                Version("2.0.0"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("==2.0.0,>=1.2.3"),
            Bounds(
                SpecifierSet("==2.0.0,>=1.2.3"),
                Version("2.0.0"),
                True,
                Version("2.0.0"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("==2.0.0,<1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("==2.0.0,<=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("==2.0.0,~=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("==2.0.0,==1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("==2.0.0,!=1.2.3"),
            Bounds(
                SpecifierSet("==2.0.0,!=1.2.3"),
                Version("2.0.0"),
                True,
                Version("2.0.0"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("!=2.0.0,>1.2.3"),
            Bounds(
                SpecifierSet("!=2.0.0,>1.2.3"),
                None,
                False,
                Version("1.2.3"),
                False,
                {Version("2.0.0")},
            ),
        ),
        (
            SpecifierSet("!=2.0.0,>=1.2.3"),
            Bounds(
                SpecifierSet("!=2.0.0,>=1.2.3"),
                None,
                False,
                Version("1.2.3"),
                True,
                {Version("2.0.0")},
            ),
        ),
        (
            SpecifierSet("!=2.0.0,<1.2.3"),
            Bounds(SpecifierSet("!=2.0.0,<1.2.3"), Version("1.2.3"), False, None, False, set()),
        ),
        (
            SpecifierSet("!=2.0.0,<=1.2.3"),
            Bounds(SpecifierSet("!=2.0.0,<=1.2.3"), Version("1.2.3"), True, None, False, set()),
        ),
        (
            SpecifierSet("!=2.0.0,~=1.2.3"),
            Bounds(
                SpecifierSet("!=2.0.0,~=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("!=2.0.0,==1.2.3"),
            Bounds(
                SpecifierSet("!=2.0.0,==1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("!=2.0.0,!=1.2.3"),
            Bounds(
                SpecifierSet("!=2.0.0,!=1.2.3"),
                None,
                False,
                None,
                False,
                {Version("1.2.3"), Version("2.0.0")},
            ),
        ),
        (
            SpecifierSet(">1.2.3,>1.2.3"),
            Bounds(SpecifierSet(">1.2.3,>1.2.3"), None, False, Version("1.2.3"), False, set()),
        ),
        (
            SpecifierSet(">1.2.3,>=1.2.3"),
            Bounds(SpecifierSet(">1.2.3,>=1.2.3"), None, False, Version("1.2.3"), False, set()),
        ),
        (
            SpecifierSet(">1.2.3,<1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">1.2.3,<=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">1.2.3,~=1.2.3"),
            Bounds(
                SpecifierSet(">1.2.3,~=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                False,
                set(),
            ),
        ),
        (
            SpecifierSet(">1.2.3,==1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">1.2.3,!=1.2.3"),
            Bounds(SpecifierSet(">1.2.3,!=1.2.3"), None, False, Version("1.2.3"), False, set()),
        ),
        (
            SpecifierSet(">=1.2.3,>1.2.3"),
            Bounds(SpecifierSet(">=1.2.3,>1.2.3"), None, False, Version("1.2.3"), False, set()),
        ),
        (
            SpecifierSet(">=1.2.3,>=1.2.3"),
            Bounds(SpecifierSet(">=1.2.3,>=1.2.3"), None, False, Version("1.2.3"), True, set()),
        ),
        (
            SpecifierSet(">=1.2.3,<1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet(">=1.2.3,<=1.2.3"),
            Bounds(
                SpecifierSet(">=1.2.3,<=1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet(">=1.2.3,~=1.2.3"),
            Bounds(
                SpecifierSet(">=1.2.3,~=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet(">=1.2.3,==1.2.3"),
            Bounds(
                SpecifierSet(">=1.2.3,==1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet(">=1.2.3,!=1.2.3"),
            Bounds(SpecifierSet(">=1.2.3,!=1.2.3"), None, False, Version("1.2.3"), False, set()),
        ),
        (
            SpecifierSet("<1.2.3,>1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("<1.2.3,>=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("<1.2.3,<1.2.3"),
            Bounds(
                SpecifierSet("<1.2.3,<1.2.3"),
                Version("1.2.3"),
                False,
                None,
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("<1.2.3,<=1.2.3"),
            Bounds(SpecifierSet("<1.2.3,<=1.2.3"), Version("1.2.3"), False, None, False, set()),
        ),
        (
            SpecifierSet("<1.2.3,~=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("<1.2.3,==1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("<1.2.3,!=1.2.3"),
            Bounds(
                SpecifierSet("<1.2.3,!=1.2.3"),
                Version("1.2.3"),
                False,
                None,
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("<=1.2.3,>1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("<=1.2.3,>=1.2.3"),
            Bounds(
                SpecifierSet("<=1.2.3,>=1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<=1.2.3,<1.2.3"),
            Bounds(SpecifierSet("<=1.2.3,<1.2.3"), Version("1.2.3"), False, None, False, set()),
        ),
        (
            SpecifierSet("<=1.2.3,<=1.2.3"),
            Bounds(SpecifierSet("<=1.2.3,<=1.2.3"), Version("1.2.3"), True, None, False, set()),
        ),
        (
            SpecifierSet("<=1.2.3,~=1.2.3"),
            Bounds(
                SpecifierSet("<=1.2.3,~=1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<=1.2.3,==1.2.3"),
            Bounds(
                SpecifierSet("<=1.2.3,==1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("<=1.2.3,!=1.2.3"),
            Bounds(
                SpecifierSet("<=1.2.3,!=1.2.3"),
                Version("1.2.3"),
                False,
                None,
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("~=1.2.3,>1.2.3"),
            Bounds(
                SpecifierSet("~=1.2.3,>1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("~=1.2.3,>=1.2.3"),
            Bounds(
                SpecifierSet("~=1.2.3,>=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("~=1.2.3,<1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("~=1.2.3,<=1.2.3"),
            Bounds(
                SpecifierSet("~=1.2.3,<=1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("~=1.2.3,~=1.2.3"),
            Bounds(
                SpecifierSet("~=1.2.3,~=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("~=1.2.3,==1.2.3"),
            Bounds(
                SpecifierSet("~=1.2.3,==1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("~=1.2.3,!=1.2.3"),
            Bounds(
                SpecifierSet("~=1.2.3,!=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("==1.2.3,>1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("==1.2.3,>=1.2.3"),
            Bounds(
                SpecifierSet("==1.2.3,>=1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("==1.2.3,<1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("==1.2.3,<=1.2.3"),
            Bounds(
                SpecifierSet("==1.2.3,<=1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("==1.2.3,~=1.2.3"),
            Bounds(
                SpecifierSet("==1.2.3,~=1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("==1.2.3,==1.2.3"),
            Bounds(
                SpecifierSet("==1.2.3,==1.2.3"),
                Version("1.2.3"),
                True,
                Version("1.2.3"),
                True,
                set(),
            ),
        ),
        (
            SpecifierSet("==1.2.3,!=1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("!=1.2.3,>1.2.3"),
            Bounds(
                SpecifierSet("!=1.2.3,>1.2.3"),
                None,
                False,
                Version("1.2.3"),
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("!=1.2.3,>=1.2.3"),
            Bounds(
                SpecifierSet("!=1.2.3,>=1.2.3"),
                None,
                False,
                Version("1.2.3"),
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("!=1.2.3,<1.2.3"),
            Bounds(SpecifierSet("!=1.2.3,<1.2.3"), Version("1.2.3"), False, None, False, set()),
        ),
        (
            SpecifierSet("!=1.2.3,<=1.2.3"),
            Bounds(SpecifierSet("!=1.2.3,<=1.2.3"), Version("1.2.3"), False, None, False, set()),
        ),
        (
            SpecifierSet("!=1.2.3,~=1.2.3"),
            Bounds(
                SpecifierSet("!=1.2.3,~=1.2.3"),
                Version("1.2.4"),
                False,
                Version("1.2.3"),
                False,
                set(),
            ),
        ),
        (
            SpecifierSet("!=1.2.3,==1.2.3"),
            AssertionError,
        ),
        (
            SpecifierSet("!=1.2.3,!=1.2.3"),
            Bounds(
                SpecifierSet("!=1.2.3,!=1.2.3"),
                None,
                False,
                None,
                False,
                {Version("1.2.3")},
            ),
        ),
    ],
    ids=specifier_set_id,
)
def test_get_bounds(specifier_set: SpecifierSet, expected: Bounds | type[Exception]) -> None:
    if isinstance(expected, Bounds):
        assert expected == get_bounds(specifier_set)
    else:
        assert isinstance(expected, type)
        with pytest.raises(expected):
            get_bounds(specifier_set)


IGNORE_SPECIFIER_SET = SpecifierSet()


@pytest.mark.parametrize(
    "bounds,exclusions,expected",
    [
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, set()),
            True,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, set()),
            True,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, {Version("1.2.4")}),
            True,
            SpecifierSet(">1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, set()),
            True,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, {Version("1.2.4")}),
            True,
            SpecifierSet(">=1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, set()),
            True,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("<2.0.0,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), False, set()),
            True,
            SpecifierSet("<2.0.0,>1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet("<2.0.0,>1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), True, set()),
            True,
            SpecifierSet("<2.0.0,>=1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet("<2.0.0,>=1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, set()),
            True,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("<=2.0.0,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), False, set()),
            True,
            SpecifierSet("<=2.0.0,>1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet("<=2.0.0,>1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), True, set()),
            True,
            SpecifierSet("<=2.0.0,>=1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet("<=2.0.0,>=1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, set()),
            False,
            IGNORE_SPECIFIER_SET,
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet(""),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, set()),
            False,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, {Version("1.2.4")}),
            False,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, set()),
            False,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, {Version("1.2.4")}),
            False,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, set()),
            False,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), False, set()),
            False,
            SpecifierSet("<2.0.0,>1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet("<2.0.0,>1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), True, set()),
            False,
            SpecifierSet("<2.0.0,>=1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet("<2.0.0,>=1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, set()),
            False,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), False, set()),
            False,
            SpecifierSet("<=2.0.0,>1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet("<=2.0.0,>1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), True, set()),
            False,
            SpecifierSet("<=2.0.0,>=1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet("<=2.0.0,>=1.2.3"),
        ),
    ],
)
def test_bounds__minimal_specifier_set(
    bounds: Bounds,
    exclusions: bool,
    expected: SpecifierSet,
) -> None:
    assert expected == bounds.minimal_specifier_set(exclusions)


@pytest.mark.parametrize(
    "bounds,exclusions,expected",
    [
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, set()),
            True,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, set()),
            True,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, {Version("1.2.4")}),
            True,
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, set()),
            True,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, {Version("1.2.4")}),
            True,
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, set()),
            True,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("<2.0.0,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), False, set()),
            True,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet("<2.0.0,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), True, set()),
            True,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet("<2.0.0,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, set()),
            True,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("<=2.0.0,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), False, set()),
            True,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet("<=2.0.0,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), True, set()),
            True,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet("<=2.0.0,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, set()),
            False,
            IGNORE_SPECIFIER_SET,
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, set()),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, {Version("1.2.4")}),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, set()),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, {Version("1.2.4")}),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, set()),
            False,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), False, set()),
            False,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), True, set()),
            False,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet("<2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, set()),
            False,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), False, set()),
            False,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), True, set()),
            False,
            SpecifierSet("<=2.0.0"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet("<=2.0.0"),
        ),
    ],
)
def test_bounds__upper_specifier_set(
    bounds: Bounds,
    exclusions: bool,
    expected: SpecifierSet,
) -> None:
    assert expected == bounds.upper_specifier_set(exclusions)


@pytest.mark.parametrize(
    "bounds,exclusions,expected",
    [
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, set()),
            True,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, set()),
            True,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, {Version("1.2.4")}),
            True,
            SpecifierSet(">1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, set()),
            True,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, {Version("1.2.4")}),
            True,
            SpecifierSet(">=1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, set()),
            True,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), False, set()),
            True,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet(">1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), True, set()),
            True,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet(">=1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, set()),
            True,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, {Version("1.2.4")}),
            True,
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), False, set()),
            True,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet(">1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), True, set()),
            True,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            True,
            SpecifierSet(">=1.2.3,!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, set()),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, set()),
            False,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, {Version("1.2.4")}),
            False,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, set()),
            False,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, {Version("1.2.4")}),
            False,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, set()),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), False, set()),
            False,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), True, set()),
            False,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, set()),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, {Version("1.2.4")}),
            False,
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), False, set()),
            False,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet(">1.2.3"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), True, set()),
            False,
            SpecifierSet(">=1.2.3"),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            False,
            SpecifierSet(">=1.2.3"),
        ),
    ],
)
def test_bounds__lower_specifier_set(
    bounds: Bounds,
    exclusions: bool,
    expected: SpecifierSet,
) -> None:
    assert expected == bounds.lower_specifier_set(exclusions)


@pytest.mark.parametrize(
    "bounds,expected",
    [
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, set()),
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, None, False, {Version("1.2.4")}),
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, set()),
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), False, {Version("1.2.4")}),
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, set()),
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, None, False, Version("1.2.3"), True, {Version("1.2.4")}),
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, set()),
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, None, False, {Version("1.2.4")}),
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), False, set()),
            SpecifierSet(),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), False, Version("1.2.3"), True, set()),
            SpecifierSet(),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                False,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, set()),
            SpecifierSet(),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, None, False, {Version("1.2.4")}),
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), False, set()),
            SpecifierSet(),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                False,
                {Version("1.2.4")},
            ),
            SpecifierSet("!=1.2.4"),
        ),
        (
            Bounds(IGNORE_SPECIFIER_SET, Version("2.0.0"), True, Version("1.2.3"), True, set()),
            SpecifierSet(),
        ),
        (
            Bounds(
                IGNORE_SPECIFIER_SET,
                Version("2.0.0"),
                True,
                Version("1.2.3"),
                True,
                {Version("1.2.4")},
            ),
            SpecifierSet("!=1.2.4"),
        ),
    ],
)
def test_bounds__exclusions_specifier_set(bounds: Bounds, expected: SpecifierSet) -> None:
    assert expected == bounds.exclusions_specifier_set()
