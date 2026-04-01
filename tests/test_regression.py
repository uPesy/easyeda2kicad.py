"""
Regression tests to ensure generated files remain consistent across versions.

This test compares the output of the current version with reference files
from a known-good version to detect any unintended changes in output.
"""

import difflib
import re
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple

import pytest
from easyeda2kicad.__main__ import main

# Test component IDs - these should be stable components from LCSC
TEST_COMPONENTS = [
    "C2856808",
    "C381116",
    "C167219",
    "C2843785",
    "C112537",
    "C97522",
    "C2838500",
    "C5364646",
    "C68740",
    "C5123977",
    "C498560",
    "C2040",
    "C154551",
    "C2685",
    "C503582",
]


class TestRegression:
    """Regression tests for file generation consistency."""

    def normalize_file_content(self, content: str) -> str:
        """Normalize file content to ignore expected differences like timestamps and temp paths."""
        lines = content.split("\n")
        normalized = []

        for line in lines:
            # Skip timestamp lines
            if "tedit" in line.lower() or "date" in line.lower():
                continue
            # Skip version comments
            if "easyeda2kicad.py" in line and "version" in line.lower():
                continue
            # Skip "Generated with" lines
            if "generated with" in line.lower():
                continue

            # Normalize temporary paths to a standard format
            # Replace /tmp/easyeda2kicad_test_XXXXX/ with /tmp/test/
            line = re.sub(r"/tmp/easyeda2kicad_test_[^/]+/", "/tmp/test/", line)
            # Also normalize other temp paths like /tmp/tmpXXXXX/
            line = re.sub(r"/tmp/tmp[a-z0-9_]+/", "/tmp/test/", line)

            normalized.append(line.rstrip())

        return "\n".join(normalized)

    def compare_files(self, ref_file: Path, new_file: Path) -> Tuple[bool, str]:
        """Compare two files and return (is_equal, unified_diff)."""
        if not ref_file.exists():
            return False, f"Reference file does not exist: {ref_file}"

        if not new_file.exists():
            return False, f"New file was not generated: {new_file}"

        with open(ref_file, "r", encoding="utf-8", errors="ignore") as f:
            ref_content = self.normalize_file_content(f.read())

        with open(new_file, "r", encoding="utf-8", errors="ignore") as f:
            new_content = self.normalize_file_content(f.read())

        if ref_content == new_content:
            return True, "Files are identical (after normalization)"

        diff = list(
            difflib.unified_diff(
                ref_content.split("\n"),
                new_content.split("\n"),
                fromfile="reference",
                tofile="new",
                lineterm="",
                n=2,
            )
        )
        return False, "\n".join(diff)

    def get_generated_files(self, output_dir: Path) -> List[Path]:
        """Get list of all generated files for a component."""
        files: list[Path] = []
        output_dir = Path(output_dir)

        # Look for symbol files
        for pattern in ["*.kicad_sym", "*.lib"]:
            files.extend(output_dir.glob(pattern))

        # Look for footprint files
        for pattern in ["*.pretty/*.kicad_mod"]:
            files.extend(output_dir.glob(pattern))

        # Look for 3D model files
        for pattern in ["*.3dshapes/*.wrl", "*.3dshapes/*.step"]:
            files.extend(output_dir.glob(pattern))

        return files

    @pytest.mark.parametrize("component_id", TEST_COMPONENTS)
    def test_symbol_generation(
        self, component_id: str, temp_output_dir: str, reference_dir: Path
    ) -> None:
        """Test that symbol files are generated consistently."""
        ref_component_dir = reference_dir / component_id / "symbols"
        if not ref_component_dir.exists():
            pytest.skip(
                f"No reference files for {component_id}. Run:\n"
                f"  pytest --create-reference {__file__}"
            )

        output_path = Path(temp_output_dir) / "test_lib"

        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--symbol",
            "--use-cache",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        symbol_files = list(Path(temp_output_dir).glob("*.kicad_sym"))
        assert len(symbol_files) > 0, "No symbol files were generated"

        for new_file in symbol_files:
            ref_file = ref_component_dir / new_file.name
            is_equal, message = self.compare_files(ref_file, new_file)
            assert is_equal, f"Symbol file differs from reference:\n{message}"

    @pytest.mark.parametrize("component_id", TEST_COMPONENTS)
    def test_footprint_generation(
        self, component_id: str, temp_output_dir: str, reference_dir: Path
    ) -> None:
        """Test that footprint files are generated consistently."""
        ref_component_dir = reference_dir / component_id / "footprints"
        if not ref_component_dir.exists():
            pytest.skip(
                f"No reference files for {component_id}. Run:\n"
                f"  pytest --create-reference {__file__}"
            )

        output_path = Path(temp_output_dir) / "test_lib"

        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--footprint",
            "--use-cache",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        footprint_files = list(Path(temp_output_dir).glob("*.pretty/*.kicad_mod"))
        assert len(footprint_files) > 0, "No footprint files were generated"

        for new_file in footprint_files:
            ref_file = ref_component_dir / new_file.name
            is_equal, message = self.compare_files(ref_file, new_file)
            assert is_equal, f"Footprint file differs from reference:\n{message}"

    @pytest.mark.parametrize("component_id", TEST_COMPONENTS)
    def test_3d_model_generation(
        self, component_id: str, temp_output_dir: str, reference_dir: Path
    ) -> None:
        """Test that 3D model files are generated consistently."""
        ref_component_dir = reference_dir / component_id / "3dmodels"
        if not ref_component_dir.exists():
            pytest.skip(
                f"No reference files for {component_id}. Run:\n"
                f"  pytest --create-reference {__file__}"
            )

        output_path = Path(temp_output_dir) / "test_lib"

        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--3d",
            "--use-cache",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        model_files = list(Path(temp_output_dir).glob("*.3dshapes/*.wrl"))
        model_files.extend(Path(temp_output_dir).glob("*.3dshapes/*.step"))

        if len(model_files) == 0:
            pytest.skip(f"No 3D model available for component {component_id}")

        for new_file in model_files:
            ref_file = ref_component_dir / new_file.name
            is_equal, message = self.compare_files(ref_file, new_file)
            assert is_equal, f"3D model file differs from reference:\n{message}"

    def test_full_generation(self, temp_output_dir: str) -> None:
        """verify --full runs without error and produces output files."""
        component_id = "C2040"
        output_path = Path(temp_output_dir) / "test_lib"

        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--full",
            "--use-cache",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        generated_files = self.get_generated_files(Path(temp_output_dir))
        assert len(generated_files) > 0, f"No files were generated in {temp_output_dir}"


# ---------------------------------------------------------------------------
# Reference file generation — run once with: pytest --create-reference
# ---------------------------------------------------------------------------


def _copy_normalized(src: Path, dst: Path) -> None:
    """Copy a file, normalizing temp paths in text files so references stay stable."""
    if src.suffix == ".step":
        shutil.copy2(src, dst)
    else:
        content = src.read_text(encoding="utf-8", errors="ignore")
        content = re.sub(r"/tmp/easyeda2kicad_test_[^/]+/", "/tmp/test/", content)
        content = re.sub(r"/tmp/tmp[a-z0-9_]+/", "/tmp/test/", content)
        dst.write_text(content, encoding="utf-8")


def test_create_reference_files(
    create_reference: bool,
    reference_dir: Path,
) -> None:
    """Create reference files for all test components. Run with --create-reference."""
    if not create_reference:
        pytest.skip("Run with --create-reference to generate reference files")

    for component_id in TEST_COMPONENTS:
        with tempfile.TemporaryDirectory(prefix="easyeda2kicad_test_") as tmp:
            output_path = Path(tmp) / "test_lib"
            args = [
                "--lcsc_id",
                component_id,
                "--output",
                str(output_path),
                "--full",
                "--use-cache",
            ]
            try:
                result = main(args)
                assert result == 0, f"main() returned error code: {result}"
            except SystemExit as e:
                assert e.code == 0, f"main() exited with code: {e.code}"

            ref_dir = reference_dir / component_id
            tmp_path = Path(tmp)

            for file in tmp_path.glob("*.kicad_sym"):
                d = ref_dir / "symbols"
                d.mkdir(parents=True, exist_ok=True)
                _copy_normalized(file, d / file.name)
                print(f"Created reference: {d / file.name}")

            for file in tmp_path.glob("*.pretty/*.kicad_mod"):
                d = ref_dir / "footprints"
                d.mkdir(parents=True, exist_ok=True)
                _copy_normalized(file, d / file.name)
                print(f"Created reference: {d / file.name}")

            for file in tmp_path.glob("*.3dshapes/*"):
                if file.is_file():
                    d = ref_dir / "3dmodels"
                    d.mkdir(parents=True, exist_ok=True)
                    _copy_normalized(file, d / file.name)
                    print(f"Created reference: {d / file.name}")

        print(f"Reference files created for {component_id}")
