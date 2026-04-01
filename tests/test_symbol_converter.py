"""Unit tests for export_kicad_symbol converter functions."""

from __future__ import annotations

import logging

import pytest

from easyeda2kicad.easyeda.parameters_easyeda import (
    EeSymbolArc,
    EeSymbolBbox,
    EeSymbolPath,
    EeSymbolPin,
    EeSymbolPinClock,
    EeSymbolPinDot,
    EeSymbolPinDotBis,
    EeSymbolPinName,
    EeSymbolPinPath,
    EeSymbolPinSettings,
    EeSymbolPolyline,
)
from easyeda2kicad.easyeda.parameters_easyeda import EasyedaPinType
from easyeda2kicad.kicad.export_kicad_symbol import (
    convert_ee_arcs,
    convert_ee_paths,
    convert_ee_pins,
    convert_ee_polylines,
    integrate_sub_units,
)
from easyeda2kicad.kicad.parameters_kicad_symbol import (
    KICAD_SYM_VERSION_20211014,
    KICAD_SYM_VERSION_20220914,
    KiPinStyle,
)


BBOX = EeSymbolBbox(x=400.0, y=300.0, width=100.0, height=100.0)


# ---- convert_ee_pins: pin styles ----


def _make_pin(dot: bool = False, clock: bool = False) -> EeSymbolPin:
    return EeSymbolPin(
        settings=EeSymbolPinSettings(
            is_displayed=True,
            type=EasyedaPinType.unspecified,
            spice_pin_number="1",
            pos_x=400,
            pos_y=300,
            rotation=0,
            id="p1",
            is_locked=False,
        ),
        pin_dot=EeSymbolPinDot(dot_x=400, dot_y=300),
        pin_path=EeSymbolPinPath(path="M 400 300 h 20", color=""),
        name=EeSymbolPinName(
            is_displayed=True,
            pos_x=400,
            pos_y=290,
            rotation=0,
            text="A",
            text_anchor="start",
            font="",
            font_size=7.0,
        ),
        dot=EeSymbolPinDotBis(is_displayed=dot, circle_x=400, circle_y=300),
        clock=EeSymbolPinClock(is_displayed=clock, path=""),
    )


def test_pin_style_inverted_clock() -> None:
    pins = convert_ee_pins([_make_pin(dot=True, clock=True)], BBOX)
    assert pins[0].style == KiPinStyle.inverted_clock


def test_pin_style_inverted() -> None:
    pins = convert_ee_pins([_make_pin(dot=True, clock=False)], BBOX)
    assert pins[0].style == KiPinStyle.inverted


def test_pin_style_clock() -> None:
    pins = convert_ee_pins([_make_pin(dot=False, clock=True)], BBOX)
    assert pins[0].style == KiPinStyle.clock


# ---- convert_ee_paths ----


def _make_path(path_str: str) -> EeSymbolPath:
    return EeSymbolPath(
        paths=path_str,
        stroke_color="",
        stroke_width="1",
        stroke_style="",
        fill_color=False,
        id="pt1",
        is_locked=False,
    )


# BBOX has origin (400, 300); EE pixel (410, 310) → KiCad mm (2.54, -2.54)
_PX = 0.0254 * 10  # 1 EE pixel = 0.254 mm


def test_convert_ee_paths_mlz() -> None:
    # M/L/Z path → closed polygon, no beziers
    path = _make_path("M 400 300 L 410 300 L 405 310 Z")
    polys, bezs = convert_ee_paths([path], BBOX)
    assert len(polys) == 1
    assert polys[0].is_closed
    assert bezs == []


def test_convert_ee_paths_pure_C(caplog: pytest.LogCaptureFixture) -> None:
    # Pure cubic bezier path (M + C) → 0 polygons, 1 bezier with 4 control points
    # M 400 300 C 402 295 408 295 410 300
    path = _make_path("M 400 300 C 402 295 408 295 410 300")
    with caplog.at_level(logging.WARNING):
        polys, bezs = convert_ee_paths([path], BBOX)
    assert polys == []
    assert len(bezs) == 1
    b = bezs[0]
    assert len(b.points) == 4
    # Start = M point (400,300) → bbox origin → (0, 0)
    assert b.points[0] == pytest.approx([0.0, 0.0], abs=1e-6)
    # End = C endpoint (410,300) → (2.54, 0)
    assert b.points[3] == pytest.approx([2.54, 0.0], abs=1e-4)
    assert "no parseable points" not in caplog.text


def test_convert_ee_paths_two_C_segments() -> None:
    # Real EasyEDA example from JS source: two chained cubic bezier segments
    # PT~M 368 282.5 C 371 290 372 290 375 282.5 C 378 275 379 275 382 282.5
    bbox = EeSymbolBbox(x=368.0, y=282.5)
    path = _make_path(
        "M 368 282.5 C 371 290 372 290 375 282.5 C 378 275 379 275 382 282.5"
    )
    polys, bezs = convert_ee_paths([path], bbox)
    assert polys == []
    assert len(bezs) == 2
    # Bezier 0: start=(368,282.5)→(0,0), end=(375,282.5)→(1.778,0)
    assert bezs[0].points[0] == pytest.approx([0.0, 0.0], abs=1e-4)
    assert bezs[0].points[3] == pytest.approx([1.778, 0.0], abs=1e-3)
    # Bezier 1: start=(375,282.5), end=(382,282.5)→(3.556,0)
    assert bezs[1].points[0] == pytest.approx([1.778, 0.0], abs=1e-3)
    assert bezs[1].points[3] == pytest.approx([3.556, 0.0], abs=1e-3)


def test_convert_ee_paths_pure_Q() -> None:
    # Q elevated to cubic; endpoint must match
    path = _make_path("M 400 300 Q 405 295 410 300")
    polys, bezs = convert_ee_paths([path], BBOX)
    assert polys == []
    assert len(bezs) == 1
    assert len(bezs[0].points) == 4
    assert bezs[0].points[0] == pytest.approx([0.0, 0.0], abs=1e-6)
    assert bezs[0].points[3] == pytest.approx([2.54, 0.0], abs=1e-4)


def test_convert_ee_paths_Q_elevation() -> None:
    # Degree-elevation formula: C1 = P0 + 2/3*(Q1-P0), C2 = Q + 2/3*(Q1-Q)
    # M (0,0) Q (6,6) (12,0) in EE pixels relative to bbox origin (0,0)
    bbox = EeSymbolBbox(x=0.0, y=0.0)
    path = _make_path("M 0 0 Q 6 6 12 0")
    _, bezs = convert_ee_paths([path], bbox)
    b = bezs[0]
    # C1 = (0,0) + 2/3*((6,6)-(0,0)) = (4, 4)  →  ki_x=4*0.254, ki_y=-(4*0.254)
    assert b.points[1] == pytest.approx([4 * _PX, -(4 * _PX)], abs=1e-6)
    # C2 = (12,0) + 2/3*((6,6)-(12,0)) = (8, 4)
    assert b.points[2] == pytest.approx([8 * _PX, -(4 * _PX)], abs=1e-6)


def test_convert_ee_paths_mixed_L_C() -> None:
    # Mixed path: L segment + C segment → polygon sub-path + bezier
    path = _make_path("M 400 300 L 405 300 C 407 295 408 295 410 300")
    polys, bezs = convert_ee_paths([path], BBOX)
    assert len(polys) == 1  # M→L segment
    assert len(bezs) == 1  # C segment
    # Polygon connects M to L (2 points)
    assert len(polys[0].points) == 2
    # Bezier starts at L endpoint (405,300) → (1.27, 0)
    assert bezs[0].points[0] == pytest.approx([1.27, 0.0], abs=1e-4)


def test_convert_ee_paths_empty_warning(caplog: pytest.LogCaptureFixture) -> None:
    path = _make_path("Z")  # Z without prior M/L → no points
    with caplog.at_level(logging.WARNING):
        polys, bezs = convert_ee_paths([path], BBOX)
    assert polys == []
    assert bezs == []
    assert "no parseable points" in caplog.text


def test_convert_ee_paths_unknown_token() -> None:
    path = _make_path("M 400 300 X 999 L 410 300")
    polys, bezs = convert_ee_paths([path], BBOX)
    assert len(polys) == 1
    assert bezs == []


def test_bezier_export_kicad7() -> None:
    # KiCad >= 20220914: emits (bezier ...) with 4 xy points
    path = _make_path("M 400 300 C 402 295 408 295 410 300")
    _, bezs = convert_ee_paths([path], BBOX)
    out = bezs[0].export(KICAD_SYM_VERSION_20220914)
    assert "(bezier" in out
    assert out.count("(xy ") == 4


def test_bezier_export_fallback_old_version() -> None:
    # KiCad < 20220914: falls back to (polyline ...) with just start + end
    path = _make_path("M 400 300 C 402 295 408 295 410 300")
    _, bezs = convert_ee_paths([path], BBOX)
    out = bezs[0].export(KICAD_SYM_VERSION_20211014)
    assert "(polyline" in out
    assert "(bezier" not in out
    assert out.count("(xy ") == 2


# ---- convert_ee_polylines: fill_color closes polygon ----


def _make_polyline(points: str, fill: bool = False) -> EeSymbolPolyline:
    return EeSymbolPolyline(
        points=points,
        stroke_color="",
        stroke_width="1",
        stroke_style="",
        fill_color=fill,
        id="pl1",
        is_locked=False,
    )


def test_polyline_fill_closes_polygon() -> None:
    pl = _make_polyline("400 300 410 300 405 310", fill=True)
    result = convert_ee_polylines([pl], BBOX)
    assert len(result) == 1
    assert result[0].is_closed


def test_polyline_no_fill_not_closed() -> None:
    pl = _make_polyline("400 300 410 300 405 310", fill=False)
    result = convert_ee_polylines([pl], BBOX)
    assert len(result) == 1
    assert not result[0].is_closed


def test_polyline_empty_points_warning(caplog: pytest.LogCaptureFixture) -> None:
    pl = _make_polyline("", fill=False)
    with caplog.at_level(logging.WARNING):
        result = convert_ee_polylines([pl], BBOX)
    assert result == []
    assert "no parseable points" in caplog.text


# ---- convert_ee_arcs: error cases ----


def _make_arc(path_str: str) -> EeSymbolArc:
    return EeSymbolArc(
        path=path_str,  # type: ignore[arg-type]  # parsed to list in __post_init__
        helper_dots="",
        stroke_color="",
        stroke_width="1",
        stroke_style="",
        fill_color=False,
        id="a1",
        is_locked=False,
    )


def test_arc_invalid_structure(caplog: pytest.LogCaptureFixture) -> None:
    arc = _make_arc("M 400 300")  # only MoveTo, no EllipticalArc
    with caplog.at_level(logging.ERROR):
        result = convert_ee_arcs([arc], BBOX)
    assert result == []
    assert "Can't convert this arc" in caplog.text


def test_arc_zero_radius(caplog: pytest.LogCaptureFixture) -> None:
    # A with radius_x=0 triggers the degenerate warning
    arc = _make_arc("M 400 300 A 0 0 0 0 1 410 300")
    with caplog.at_level(logging.WARNING):
        result = convert_ee_arcs([arc], BBOX)
    assert result == []
    assert "degenerate arc" in caplog.text


# ---- integrate_sub_units ----


def test_integrate_sub_units_empty() -> None:
    main = '(symbol "Foo_0_1" (pin) )'
    assert integrate_sub_units(main, [], "Foo") == main


def test_integrate_sub_units_no_match() -> None:
    main = '(symbol "Foo_0_1" (pin) )'
    sub = '(symbol "Bar_0_1" (pin) )'
    assert integrate_sub_units(main, [sub], "Foo") == main


def test_integrate_sub_units_replaces() -> None:
    main = '  (symbol "Foo_0_1"\n    (pin)\n  )\n'
    sub = '  (symbol "Foo_0_1"\n    (pin)\n  )\n'
    result = integrate_sub_units(main, [sub], "Foo")
    assert '"Foo_1_1"' in result
    assert '"Foo_0_1"' not in result
