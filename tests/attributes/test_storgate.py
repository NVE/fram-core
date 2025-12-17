from unittest.mock import Mock

import pytest

from framcore.attributes.level_profile_attributes import StockVolume
from framcore.attributes.Storage import Storage


@pytest.mark.parametrize("percentage", [1.1, -0.1])
def test_init_illegal_storage_percentage(percentage: float):
    with pytest.raises(ValueError, match=f"^Value {percentage} is"):
        Storage(capacity=Mock(spec=StockVolume), initial_storage_percentage=percentage)

def test_init_legal_storage_percentage():
    try:
        Storage(capacity=Mock(spec=StockVolume), initial_storage_percentage=0.5)
    except ValueError:
        pytest.fail("Storage raised ValueError unexpectedly!")
