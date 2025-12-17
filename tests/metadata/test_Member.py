from unittest.mock import Mock

import pytest

from framcore.metadata import Div, Member, Meta


def test_init_valid_input():
    member = Member(value="valid_string")

    assert member.get_value() == "valid_string"


@pytest.mark.parametrize(
    "invalid_value",
    [
        42,
        3.14,
        ["invalid_list"],
        None,
    ],
)
def test_init_invalid_input_raises(invalid_value):
    with pytest.raises(TypeError):
        Member(value=invalid_value)


@pytest.mark.parametrize(
    ("value1", "value2", "expected_equal"),
    [
        ("same", "same", True),
        ("same", "different", False),
    ],
)
def test_eq(value1, value2, expected_equal):
    member1 = Member(value=value1)
    member2 = Member(value=value2)

    assert (member1 == member2) == expected_equal


@pytest.mark.parametrize(
    ("value1", "value2", "expected_equal"),
    [
        ("same", "same", True),
        ("same", "different", False),
    ],
)
def test_hash(value1, value2, expected_equal):
    member1 = Member(value=value1)
    member2 = Member(value=value2)

    assert (hash(member1) == hash(member2)) == expected_equal


def test_combine_with_same_member_returns_self():
    member1 = Member(value="same")
    member2 = Member(value="same")

    combined = member1.combine(member2)

    assert combined is member1


def test_combine_with_different_member_returns_div():
    member1 = Member(value="first")
    member2 = Member(value="second")

    combined = member1.combine(member2)

    assert isinstance(combined, Div)
    assert member1 in combined.get_value()
    assert member2 in combined.get_value()


def test_combine_with_other_meta_returns_div():
    member = Member(value="member")
    other_meta = Mock(Meta)

    combined = member.combine(other_meta)

    assert isinstance(combined, Div)
    assert member in combined.get_value()
    assert other_meta in combined.get_value()


def test_get_fingerprint_same_for_equal_members():
    member1 = Member(value="same")
    member2 = Member(value="same")

    assert member1.get_fingerprint() == member2.get_fingerprint()


def test_get_fingerprint_different_for_unequal_members():
    member1 = Member(value="first")
    member2 = Member(value="second")

    assert member1.get_fingerprint() != member2.get_fingerprint()
