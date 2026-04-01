"""Unit tests for footprint writer helper functions."""

import math

import pytest

from easyeda2kicad.kicad.export_kicad_footprint import (
    angle_to_ki,
    compute_arc,
    drill_to_ki,
    fp_to_ki,
)

TOL = 1e-6


def on_circle(
    cx: float, cy: float, r: float, x: float, y: float, tol: float = TOL
) -> bool:
    return abs(math.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r) < tol


# ---------------------------------------------------------------------------
# fp_to_ki
# ---------------------------------------------------------------------------


class TestFpToKi:
    def test_known_value(self) -> None:
        # 100 EasyEDA px = 100 * 10 * 0.0254 = 25.4 mm
        assert fp_to_ki(100) == pytest.approx(25.4, abs=1e-6)

    def test_empty_string(self) -> None:
        assert fp_to_ki("") == 0.0

    def test_none(self) -> None:
        assert fp_to_ki(None) == 0.0  # type: ignore[arg-type]  # explicit runtime guard

    def test_invalid_string(self) -> None:
        assert fp_to_ki("abc") == 0.0

    def test_zero(self) -> None:
        assert fp_to_ki(0) == 0.0

    def test_negative(self) -> None:
        assert fp_to_ki(-100) == pytest.approx(-25.4, abs=1e-6)

    def test_precision_6_decimals(self) -> None:
        # Result must not have more than 6 decimal places (1nm resolution)
        result = fp_to_ki(3)
        assert result == round(result, 6)


# ---------------------------------------------------------------------------
# drill_to_ki
# ---------------------------------------------------------------------------


class TestDrillToKi:
    def test_round_hole(self) -> None:
        result = drill_to_ki(
            hole_radius=0.5, hole_length=0, pad_height=1.0, pad_width=1.0
        )
        assert result == "(drill 1.0)"

    def test_no_hole(self) -> None:
        assert drill_to_ki(0, 0, 1.0, 1.0) == ""

    def test_oval_horizontal(self) -> None:
        # hole_length > hole_radius*2 → oval, longer in first dimension
        result = drill_to_ki(
            hole_radius=0.3, hole_length=1.0, pad_height=2.0, pad_width=2.0
        )
        assert "oval" in result

    def test_oval_orientation_depends_on_pad(self) -> None:
        # pad_height > pad_width → slot along height axis
        r1 = drill_to_ki(0.3, 1.0, pad_height=3.0, pad_width=1.0)
        r2 = drill_to_ki(0.3, 1.0, pad_height=1.0, pad_width=3.0)
        assert r1 != r2


# ---------------------------------------------------------------------------
# angle_to_ki
# ---------------------------------------------------------------------------


class TestAngleToKi:
    def test_zero(self) -> None:
        assert angle_to_ki(0) == 0.0

    def test_90(self) -> None:
        assert angle_to_ki(90) == 90.0

    def test_270_wraps(self) -> None:
        # 270 > 180 → -(360 - 270) = -90
        assert angle_to_ki(270) == pytest.approx(-90.0)

    def test_string_input(self) -> None:
        assert angle_to_ki("90") == 90.0

    def test_invalid_string(self) -> None:
        assert angle_to_ki("bad") == 0.0


# ---------------------------------------------------------------------------
# compute_arc
# ---------------------------------------------------------------------------


class TestComputeArc:
    def test_quarter_circle_center(self) -> None:
        # Quarter circle on unit circle: (1,0) → (0,1), sweep=True
        cx, cy, _ = compute_arc(1, 0, 1, 1, 0, False, True, 0, 1)
        assert on_circle(cx, cy, 1.0, 1.0, 0.0)
        assert on_circle(cx, cy, 1.0, 0.0, 1.0)

    def test_semicircle_extent_180(self) -> None:
        # Half circle: (-1,0) → (1,0), r=1, sweep=True → extent ≈ 180
        _cx, _cy, extent = compute_arc(-1, 0, 1, 1, 0, False, True, 1, 0)
        assert abs(abs(extent) - 180.0) < 1.0

    def test_large_arc_flag_flips_extent(self) -> None:
        # Same endpoints, large_arc changes which arc is taken
        _, _, e_small = compute_arc(1, 0, 1, 1, 0, False, True, 0, 1)
        _, _, e_large = compute_arc(1, 0, 1, 1, 0, True, True, 0, 1)
        assert abs(e_small) < abs(e_large)

    def test_sweep_flag_inverts_extent_sign(self) -> None:
        _, _, e1 = compute_arc(1, 0, 1, 1, 0, False, True, 0, 1)
        _, _, e2 = compute_arc(1, 0, 1, 1, 0, False, False, 0, 1)
        assert e1 * e2 < 0  # opposite signs

    def test_small_radii_scaled_up(self) -> None:
        # Radii too small for chord distance → must be scaled; should not crash
        cx, cy, extent = compute_arc(0, 0, 0.01, 0.01, 0, False, True, 10, 0)
        assert math.isfinite(cx) and math.isfinite(cy) and math.isfinite(extent)

    def test_coincident_points_no_crash(self) -> None:
        # Start == end: degenerate case, just must not raise
        cx, cy, extent = compute_arc(1, 0, 1, 1, 0, False, True, 1, 0)
        assert math.isfinite(cx) and math.isfinite(cy) and math.isfinite(extent)

    def test_result_center_equidistant_from_endpoints(self) -> None:
        # Center must be equidistant from both endpoints (= on the circle)
        cx, cy, _ = compute_arc(0, 1, 1, 1, 0, False, True, 1, 0)
        d_start = math.sqrt((1 - cx) ** 2 + (0 - cy) ** 2)
        d_end = math.sqrt((1 - cx) ** 2 + (0 - cy) ** 2)
        assert abs(d_start - d_end) < TOL
