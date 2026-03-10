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
from easyeda2kicad.kicad.parameters_kicad_symbol import KiPinStyle


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


# ---- convert_ee_paths: curve commands and edge cases ----


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


def test_convert_ee_paths_mlz() -> None:
    path = _make_path("M 400 300 L 410 300 L 405 310 Z")
    result = convert_ee_paths([path], BBOX)
    assert len(result) == 1
    assert result[0].is_closed


def test_convert_ee_paths_curve_C(caplog: pytest.LogCaptureFixture) -> None:
    # C: x1 y1 x2 y2 x y — endpoint at idx+5, idx+6
    path = _make_path("M 400 300 C 402 295 408 295 410 300")
    with caplog.at_level(logging.WARNING):
        result = convert_ee_paths([path], BBOX)
    assert len(result) == 1
    assert "curve commands" in caplog.text


def test_convert_ee_paths_curve_Q(caplog: pytest.LogCaptureFixture) -> None:
    # Q: x1 y1 x y
    path = _make_path("M 400 300 Q 405 295 410 300")
    with caplog.at_level(logging.WARNING):
        result = convert_ee_paths([path], BBOX)
    assert len(result) == 1
    assert "curve commands" in caplog.text


def test_convert_ee_paths_curve_A(caplog: pytest.LogCaptureFixture) -> None:
    # A: rx ry rot fA fS x y
    path = _make_path("M 400 300 A 5 5 0 0 1 410 300")
    with caplog.at_level(logging.WARNING):
        result = convert_ee_paths([path], BBOX)
    assert len(result) == 1
    assert "curve commands" in caplog.text


def test_convert_ee_paths_empty_warning(caplog: pytest.LogCaptureFixture) -> None:
    path = _make_path("Z")  # Z without prior M/L → no points
    with caplog.at_level(logging.WARNING):
        result = convert_ee_paths([path], BBOX)
    assert result == []
    assert "no parseable points" in caplog.text


def test_convert_ee_paths_unknown_token() -> None:
    # Unknown token should be skipped without error
    path = _make_path("M 400 300 X 999 L 410 300")
    result = convert_ee_paths([path], BBOX)
    assert len(result) == 1


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
