"""Unit tests for symbol library helper functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from easyeda2kicad.kicad.export_kicad_symbol import (
    id_already_in_symbol_lib,
    read_symbol_lib_version,
    write_component_in_symbol_lib_file,
)


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
    write_component_in_symbol_lib_file(str(v6_lib), "CompA", V6_SYMBOL_A)
    return v6_lib


# ---- id_already_in_symbol_lib ----


def test_id_not_in_empty_lib(v6_lib: Path) -> None:
    assert not id_already_in_symbol_lib(str(v6_lib), "CompA")


def test_id_found_after_add(v6_lib_with_a: Path) -> None:
    assert id_already_in_symbol_lib(str(v6_lib_with_a), "CompA")


def test_id_not_found_different_name(v6_lib_with_a: Path) -> None:
    assert not id_already_in_symbol_lib(str(v6_lib_with_a), "CompB")


# ---- write_component_in_symbol_lib_file (insert) ----


def test_write_inserts_before_closing_paren(v6_lib: Path) -> None:
    write_component_in_symbol_lib_file(str(v6_lib), "CompA", V6_SYMBOL_A)
    content = v6_lib.read_text(encoding="utf-8")
    assert '"CompA"' in content
    assert content.rstrip().endswith(")")


def test_write_two_components(v6_lib: Path) -> None:
    write_component_in_symbol_lib_file(str(v6_lib), "CompA", V6_SYMBOL_A)
    write_component_in_symbol_lib_file(str(v6_lib), "CompB", V6_SYMBOL_B)
    content = v6_lib.read_text(encoding="utf-8")
    assert '"CompA"' in content
    assert '"CompB"' in content


def test_write_creates_lib_if_missing(tmp_path: Path) -> None:
    lib = tmp_path / "new.kicad_sym"
    write_component_in_symbol_lib_file(str(lib), "CompA", V6_SYMBOL_A)
    content = lib.read_text(encoding="utf-8")
    assert '"CompA"' in content
    assert "kicad_symbol_lib" in content


# ---- write_component_in_symbol_lib_file (overwrite) ----


def test_overwrite_does_not_duplicate_symbol(v6_lib_with_a: Path) -> None:
    """Writing the same symbol again must not create a second copy."""
    write_component_in_symbol_lib_file(str(v6_lib_with_a), "CompA", V6_SYMBOL_A)
    content = v6_lib_with_a.read_text(encoding="utf-8")
    assert content.count('(symbol "CompA"') == 1


def test_overwrite_replaces_content(v6_lib_with_a: Path) -> None:
    """Writing updated content replaces the old symbol."""
    updated = V6_SYMBOL_A.replace("CompA_0_1", "CompA_0_1_updated")
    write_component_in_symbol_lib_file(str(v6_lib_with_a), "CompA", updated)
    content = v6_lib_with_a.read_text(encoding="utf-8")
    assert "CompA_0_1_updated" in content
    assert content.count('"CompA"') == 1


def test_overwrite_leaves_other_components_intact(v6_lib_with_a: Path) -> None:
    """Overwriting CompA must not touch CompB."""
    write_component_in_symbol_lib_file(str(v6_lib_with_a), "CompB", V6_SYMBOL_B)
    write_component_in_symbol_lib_file(str(v6_lib_with_a), "CompA", V6_SYMBOL_A)
    content = v6_lib_with_a.read_text(encoding="utf-8")
    assert content.count('(symbol "CompA"') == 1
    assert content.count('(symbol "CompB"') == 1


def test_write_two_then_overwrite_first_unchanged(v6_lib_with_a: Path) -> None:
    """Two components: overwriting first with same content leaves lib semantically unchanged."""
    write_component_in_symbol_lib_file(str(v6_lib_with_a), "CompB", V6_SYMBOL_B)
    content_before = v6_lib_with_a.read_text(encoding="utf-8")

    write_component_in_symbol_lib_file(str(v6_lib_with_a), "CompA", V6_SYMBOL_A)
    content_after = v6_lib_with_a.read_text(encoding="utf-8")

    assert content_after.count('(symbol "CompA"') == 1
    assert content_after.count('(symbol "CompB"') == 1
    assert content_before.strip() == content_after.strip()


# ---- read_symbol_lib_version ----


def test_read_version_exact_known(tmp_path: Path) -> None:
    """Exact known version is returned unchanged."""
    lib = tmp_path / "test.kicad_sym"
    lib.write_text("(kicad_symbol_lib\n  (version 20230620)\n)", encoding="utf-8")
    assert read_symbol_lib_version(str(lib)) == 20230620


def test_read_version_between_two_known(tmp_path: Path) -> None:
    """Version between two known ones maps to the next older known version."""
    lib = tmp_path / "test.kicad_sym"
    lib.write_text("(kicad_symbol_lib\n  (version 20221001)\n)", encoding="utf-8")
    assert read_symbol_lib_version(str(lib)) == 20220914


def test_read_version_newer_than_all_known(tmp_path: Path) -> None:
    """Version newer than all known ones maps to the newest known version."""
    lib = tmp_path / "test.kicad_sym"
    lib.write_text("(kicad_symbol_lib\n  (version 99991231)\n)", encoding="utf-8")
    assert read_symbol_lib_version(str(lib)) == 20251024


def test_read_version_older_than_all_known(tmp_path: Path) -> None:
    """Version older than all known ones falls back to the oldest known version."""
    lib = tmp_path / "test.kicad_sym"
    lib.write_text("(kicad_symbol_lib\n  (version 20200101)\n)", encoding="utf-8")
    assert read_symbol_lib_version(str(lib)) == 20211014


def test_read_version_missing_version_field(tmp_path: Path) -> None:
    """File without a version field falls back to the oldest known version."""
    lib = tmp_path / "test.kicad_sym"
    lib.write_text("(kicad_symbol_lib\n)", encoding="utf-8")
    assert read_symbol_lib_version(str(lib)) == 20211014


def test_read_version_file_not_found() -> None:
    """Non-existent file falls back to the oldest known version."""
    assert read_symbol_lib_version("/nonexistent/path/test.kicad_sym") == 20211014


def test_read_version_none() -> None:
    """None as lib_path falls back to the oldest known version."""
    assert read_symbol_lib_version(None) == 20211014
