import math
from pango_feature_demos import hsla_to_rgba

def test_hsla_to_rgba_identity():
    # pure red, full lightness
    r, g, b, a = hsla_to_rgba((0.0, 1.0, 0.5, 1.0))
    assert math.isclose(r, 1.0, abs_tol=1e-3)
    assert math.isclose(g, 0.0, abs_tol=1e-3)
    assert math.isclose(b, 0.0, abs_tol=1e-3)
    assert a == 1.0


def test_hsla_to_rgba_transparent():
    rgba = hsla_to_rgba((0.3, 0.8, 0.4, 0.2))
    # only check alpha preserved
    assert math.isclose(rgba[3], 0.2, abs_tol=1e-6)
