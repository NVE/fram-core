from unittest.mock import Mock

from framcore.curves import LoadedCurve
from framcore.loaders import CurveLoader


def test_init_minimal_args():
    loader = Mock(spec=CurveLoader)
    loader.get_x_axis.return_value = [0, 1, 2]
    loader.get_y_axis.return_value = [10, 20, 30]
    loader.get_x_unit.return_value = "hours"
    loader.get_y_unit.return_value = "kW"
    curve = LoadedCurve(curve_id="curve", loader=loader)

    assert curve.get_unique_name() == "curve"
    assert curve.get_x_axis(is_float32=False) == [0, 1, 2]
    assert curve.get_y_axis(is_float32=False) == [10, 20, 30]
    assert curve.get_x_unit() == "hours"
    assert curve.get_y_unit() == "kW"
    assert curve.get_loader() is loader
