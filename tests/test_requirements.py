import pytest
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

import compreq as cr


def test_optional_requirement() -> None:
    requirement = Requirement("foo[extra] @ http://my.url.com/file.tag.gz")
    optional = cr.OptionalRequirement(requirement, optional=True)

    assert requirement == optional.requirement
    assert True is optional.optional
    assert optional.name == "foo"
    assert optional.url == "http://my.url.com/file.tag.gz"
    assert {"extra"} == optional.extras
    assert SpecifierSet() == optional.specifier
    assert optional.marker is None

    requirement = Requirement("foo<2.0,>=1.2 ; python_version>='3.9'")
    optional = cr.OptionalRequirement(requirement, optional=False)

    assert requirement == optional.requirement
    assert False is optional.optional
    assert optional.name == "foo"
    assert optional.url is None
    assert not optional.extras
    assert SpecifierSet("<2.0,>=1.2") == optional.specifier
    assert Marker("python_version>='3.9'") == optional.marker


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            "foo<2.0,>=1.3",
            cr.OptionalRequirement(Requirement("foo<2.0,>=1.3"), optional=False),
        ),
        (
            Requirement("foo<2.0,>=1.3"),
            cr.OptionalRequirement(Requirement("foo<2.0,>=1.3"), optional=False),
        ),
        (
            cr.OptionalRequirement(Requirement("foo<2.0,>=1.3"), optional=True),
            cr.OptionalRequirement(Requirement("foo<2.0,>=1.3"), optional=True),
        ),
    ],
)
def test_get_optional_requirement(
    requirement: cr.AnyOptionalRequirement,
    expected: cr.OptionalRequirement,
) -> None:
    assert expected == cr.get_optional_requirement(requirement)


def test_requirement_set() -> None:
    requirement_1 = cr.OptionalRequirement(Requirement("foo_1"), True)
    requirement_2 = cr.OptionalRequirement(Requirement("foo_2"), False)
    requirement_set = cr.get_requirement_set([requirement_1, requirement_2])

    assert len(requirement_set) == 2
    assert {
        "foo_1": requirement_1,
        "foo_2": requirement_2,
    } == dict(requirement_set)
    assert "foo_1" in requirement_set
    assert requirement_1 == requirement_set["foo_1"]
    assert "foo_3" not in requirement_set
    assert bool(requirement_set)


def test_requirement_set__empty() -> None:
    requirement_set = cr.get_requirement_set([])

    assert len(requirement_set) == 0
    assert dict(requirement_set) == {}
    assert "foo_1" not in requirement_set
    assert not bool(requirement_set)


@pytest.mark.parametrize(
    "requirement_set,expected",
    [
        (
            "foo<2.0,>=1.3",
            cr.RequirementSet(
                {
                    "foo": cr.OptionalRequirement(Requirement("foo<2.0,>=1.3"), optional=False),
                },
            ),
        ),
        (
            Requirement("foo<2.0,>=1.3"),
            cr.RequirementSet(
                {
                    "foo": cr.OptionalRequirement(Requirement("foo<2.0,>=1.3"), optional=False),
                },
            ),
        ),
        (
            cr.OptionalRequirement(Requirement("foo<2.0,>=1.3"), optional=True),
            cr.RequirementSet(
                {
                    "foo": cr.OptionalRequirement(Requirement("foo<2.0,>=1.3"), optional=True),
                },
            ),
        ),
        (
            [
                "foo1==1.1",
                Requirement("foo2==1.2"),
                cr.OptionalRequirement(Requirement("foo3==1.3"), optional=True),
            ],
            cr.RequirementSet(
                {
                    "foo1": cr.OptionalRequirement(Requirement("foo1==1.1"), optional=False),
                    "foo2": cr.OptionalRequirement(Requirement("foo2==1.2"), optional=False),
                    "foo3": cr.OptionalRequirement(Requirement("foo3==1.3"), optional=True),
                },
            ),
        ),
        (
            {
                "foo1": "foo1==1.1",
                "foo2": Requirement("foo2==1.2"),
                "foo3": cr.OptionalRequirement(Requirement("foo3==1.3"), optional=True),
            },
            cr.RequirementSet(
                {
                    "foo1": cr.OptionalRequirement(Requirement("foo1==1.1"), optional=False),
                    "foo2": cr.OptionalRequirement(Requirement("foo2==1.2"), optional=False),
                    "foo3": cr.OptionalRequirement(Requirement("foo3==1.3"), optional=True),
                },
            ),
        ),
    ],
)
def test_get_requirement_set(
    requirement_set: cr.AnyRequirementSet_,
    expected: cr.RequirementSet,
) -> None:
    assert expected == cr.get_requirement_set(requirement_set)
