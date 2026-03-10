"""Unit tests for symbol library helper functions (add, update, id_already_in)."""

from __future__ import annotations

from pathlib import Path

import pytest

from easyeda2kicad.helpers import (
    add_component_in_symbol_lib_file,
    id_already_in_symbol_lib,
    update_component_in_symbol_lib_file,
)
from easyeda2kicad.kicad.parameters_kicad_symbol import KicadVersion


# ---- fixtures ----

V6_LIB_HEADER = """\
(kicad_symbol_lib
\t(version 20241209)
\t(generator "easyeda2kicad")
)"""

V6_SYMBOL_A = """\

  (symbol "CompA"
    (in_bom yes) (on_board yes)
    (symbol "CompA_0_1"
    )
  )
"""

V6_SYMBOL_B = """\

  (symbol "CompB"
    (in_bom yes) (on_board yes)
    (symbol "CompB_0_1"
    )
  )
"""


@pytest.fixture()
def v6_lib(tmp_path: Path) -> Path:
    lib = tmp_path / "test.kicad_sym"
    lib.write_text(V6_LIB_HEADER, encoding="utf-8")
    return lib


@pytest.fixture()
def v6_lib_with_a(v6_lib: Path) -> Path:
    add_component_in_symbol_lib_file(str(v6_lib), V6_SYMBOL_A)
    return v6_lib


# ---- id_already_in_symbol_lib ----


def test_id_not_in_empty_lib(v6_lib: Path) -> None:
    assert not id_already_in_symbol_lib(str(v6_lib), "CompA", KicadVersion.v6)


def test_id_found_after_add(v6_lib_with_a: Path) -> None:
    assert id_already_in_symbol_lib(str(v6_lib_with_a), "CompA", KicadVersion.v6)


def test_id_not_found_different_name(v6_lib_with_a: Path) -> None:
    assert not id_already_in_symbol_lib(str(v6_lib_with_a), "CompB", KicadVersion.v6)


# ---- add_component_in_symbol_lib_file ----


def test_add_inserts_before_closing_paren(v6_lib: Path) -> None:
    add_component_in_symbol_lib_file(str(v6_lib), V6_SYMBOL_A)
    content = v6_lib.read_text(encoding="utf-8")
    assert '"CompA"' in content
    assert content.rstrip().endswith(")")


def test_add_two_components(v6_lib: Path) -> None:
    add_component_in_symbol_lib_file(str(v6_lib), V6_SYMBOL_A)
    add_component_in_symbol_lib_file(str(v6_lib), V6_SYMBOL_B)
    content = v6_lib.read_text(encoding="utf-8")
    assert '"CompA"' in content
    assert '"CompB"' in content


# ---- update_component_in_symbol_lib_file (overwrite) ----


def test_overwrite_does_not_duplicate_symbol(v6_lib_with_a: Path) -> None:
    """Overwriting with identical content must not create a second copy."""
    update_component_in_symbol_lib_file(
        str(v6_lib_with_a), "CompA", V6_SYMBOL_A, KicadVersion.v6
    )
    content = v6_lib_with_a.read_text(encoding="utf-8")
    assert content.count('(symbol "CompA"') == 1


def test_overwrite_replaces_content(v6_lib_with_a: Path) -> None:
    """Overwriting with new content replaces the old symbol, not appends."""
    V6_SYMBOL_A_UPDATED = V6_SYMBOL_A.replace("CompA_0_1", "CompA_0_1_updated")
    update_component_in_symbol_lib_file(
        str(v6_lib_with_a), "CompA", V6_SYMBOL_A_UPDATED, KicadVersion.v6
    )
    content = v6_lib_with_a.read_text(encoding="utf-8")
    assert "CompA_0_1_updated" in content
    assert content.count('"CompA"') == 1  # only one occurrence


def test_overwrite_two_components_first_unchanged(v6_lib_with_a: Path) -> None:
    """Two components in lib: overwriting first with same content leaves lib semantically unchanged."""
    add_component_in_symbol_lib_file(str(v6_lib_with_a), V6_SYMBOL_B)
    content_before = v6_lib_with_a.read_text(encoding="utf-8")

    update_component_in_symbol_lib_file(
        str(v6_lib_with_a), "CompA", V6_SYMBOL_A, KicadVersion.v6
    )
    content_after = v6_lib_with_a.read_text(encoding="utf-8")

    # Both components still present exactly once
    assert content_after.count('(symbol "CompA"') == 1
    assert content_after.count('(symbol "CompB"') == 1
    # Semantic content identical (ignoring trailing whitespace differences)
    assert content_before.strip() == content_after.strip()


def test_overwrite_leaves_other_components_intact(v6_lib_with_a: Path) -> None:
    """Overwriting CompA must not touch CompB."""
    add_component_in_symbol_lib_file(str(v6_lib_with_a), V6_SYMBOL_B)
    update_component_in_symbol_lib_file(
        str(v6_lib_with_a), "CompA", V6_SYMBOL_A, KicadVersion.v6
    )
    content = v6_lib_with_a.read_text(encoding="utf-8")
    assert '"CompB"' in content
