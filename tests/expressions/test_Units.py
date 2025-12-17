import pytest

from framcore.expressions import get_unit_conversion_factor
from framcore.expressions.units import is_convertable


@pytest.mark.parametrize(
    ("from_unit", "to_unit"),
    [
        ("MW", "MW"),
        ("m3", "m3"),
    ],
)
def test_same_unit_returns_one(from_unit, to_unit):
    assert get_unit_conversion_factor(from_unit, to_unit) == 1.0


@pytest.mark.parametrize(
    ("from_unit", "to_unit", "expected"),
    [
        ("MW", "GW", 0.001),
        ("MWh", "TWh", 1e-6),
        ("m3", "Mm3", 1e-6),
        ("EUR/MWh", "EUR/GWh", 1000.0),
    ],
)
def test_known_fastpath_conversions(from_unit, to_unit, expected):
    assert get_unit_conversion_factor(from_unit, to_unit) == expected


@pytest.mark.parametrize(
    ("from_unit", "to_unit", "expected"),
    [
        ("2*MW", "GW", 0.002),
        ("2*kW", "MW", 0.002),
        ("1000*m3", "Mm3", 0.001),
    ],
)
def test_multiplier_in_from_unit(from_unit, to_unit, expected):
    assert get_unit_conversion_factor(from_unit, to_unit) == expected


@pytest.mark.parametrize(
    ("from_unit", "to_unit", "expected"),
    [
        ("MW", "kW", 1000.0),    # 1 MW = 1000 kW
        ("GWh", "MWh", 1000.0),  # 1 GWh = 1000 MWh
    ],
)
def test_fallback_conversion(from_unit, to_unit, expected):
    assert pytest.approx(get_unit_conversion_factor(from_unit, to_unit), rel=1e-12) == expected


@pytest.mark.parametrize(
    ("from_unit", "to_unit"),
    [
        ("MW", "m3/s"),
        ("m3/s", "MW"),
        ("GWh", "Mm3"),
        ("Mm3", "GWh"),
    ],
)
def test_incompatible_units_raises(from_unit, to_unit):
    with pytest.raises(ValueError, match=".+"):
        get_unit_conversion_factor(from_unit, to_unit)


@pytest.mark.parametrize(
    ("from_unit", "to_unit"),
    [
        (None, "MW"),
        ("MW", None),
    ],
)
def test_none_units_raise(from_unit, to_unit):
    with pytest.raises(ValueError, match=".+"):
        get_unit_conversion_factor(from_unit, to_unit)


@pytest.mark.parametrize(
    ("from_unit", "to_unit"),
    [
        ("foobar", "MW"),
        ("MW", "foobar"),
    ],
)
def test_unknown_unit_raises(from_unit, to_unit):
    with pytest.raises(ValueError, match=".+"):
        get_unit_conversion_factor(from_unit, to_unit)

@pytest.mark.parametrize(
    ("from_unit", "to_unit", "expected"),
    [
        ("MW", "GW", True),
        ("GW", "MW", True),
        ("m3", "Mm3", True),
        ("Mm3", "m3", True),
        ("foobar", "MW", False),
        ("MW", "foobar", False),
    ],
)
def test_is_convertable(from_unit: str, to_unit: str, expected: bool):
    result = is_convertable(from_unit, to_unit)
    assert result is expected
