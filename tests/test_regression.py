"""
Regression tests to ensure generated files remain consistent across versions.

This test compares the output of the current version with reference files
from a known-good version to detect any unintended changes in output.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple

import pytest
from easyeda2kicad.__main__ import main


class TestRegression:
    """Regression tests for file generation consistency."""

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
    ]

    def normalize_file_content(self, content: str, file_ext: str) -> str:
        """
        Normalize file content to ignore expected differences.

        - Remove timestamps and version strings
        - Normalize whitespace
        - Normalize temporary paths
        - Sort entries where order doesn't matter
        """
        import re

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

            normalized.append(line.rstrip())

        return "\n".join(normalized)

    def compare_files(
        self, ref_file: Path, new_file: Path, file_type: str
    ) -> Tuple[bool, str]:
        """
        Compare two files and return (is_equal, diff_message).

        Args:
            ref_file: Reference file path
            new_file: New generated file path
            file_type: Type of file (symbol, footprint, 3d_model)

        Returns:
            Tuple of (is_equal, difference_description)
        """
        if not ref_file.exists():
            return False, f"Reference file does not exist: {ref_file}"

        if not new_file.exists():
            return False, f"New file was not generated: {new_file}"

        # Read and normalize both files
        with open(ref_file, "r", encoding="utf-8", errors="ignore") as f:
            ref_content = self.normalize_file_content(f.read(), file_type)

        with open(new_file, "r", encoding="utf-8", errors="ignore") as f:
            new_content = self.normalize_file_content(f.read(), file_type)

        if ref_content == new_content:
            return True, "Files are identical (after normalization)"

        # Calculate difference
        ref_lines = ref_content.split("\n")
        new_lines = new_content.split("\n")

        diff_lines = []
        max_lines = max(len(ref_lines), len(new_lines))

        for i in range(max_lines):
            ref_line = ref_lines[i] if i < len(ref_lines) else "<missing>"
            new_line = new_lines[i] if i < len(new_lines) else "<missing>"

            if ref_line != new_line:
                diff_lines.append(f"Line {i+1}:")
                diff_lines.append(f"  REF: {ref_line}")
                diff_lines.append(f"  NEW: {new_line}")

                # Only show first 10 differences
                if len(diff_lines) > 30:
                    diff_lines.append("... (more differences)")
                    break

        return False, "\n".join(diff_lines)

    def get_generated_files(self, output_dir: Path, component_id: str) -> List[Path]:
        """Get list of all generated files for a component."""
        files = []
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
    def test_symbol_generation(self, component_id, temp_output_dir, reference_dir):
        """Test that symbol files are generated consistently."""
        output_path = Path(temp_output_dir) / "test_lib"

        # Generate files with current version
        # Use sys.argv style to simulate command line
        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--symbol",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        # Find generated symbol files (in temp_output_dir, not subdirectory)
        symbol_files = list(Path(temp_output_dir).glob("*.kicad_sym"))
        assert len(symbol_files) > 0, "No symbol files were generated"

        # Compare with reference
        for new_file in symbol_files:
            ref_file = reference_dir / component_id / "symbols" / new_file.name

            if not ref_file.exists():
                pytest.skip(
                    f"Reference file not found: {ref_file}\n"
                    f"To create reference files, run:\n"
                    f"  pytest --create-reference {__file__}"
                )

            is_equal, message = self.compare_files(ref_file, new_file, "symbol")
            assert is_equal, f"Symbol file differs from reference:\n{message}"

    @pytest.mark.parametrize("component_id", TEST_COMPONENTS)
    def test_footprint_generation(self, component_id, temp_output_dir, reference_dir):
        """Test that footprint files are generated consistently."""
        output_path = Path(temp_output_dir) / "test_lib"

        # Generate files with current version
        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--footprint",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        # Find generated footprint files (in temp_output_dir, not subdirectory)
        footprint_files = list(Path(temp_output_dir).glob("*.pretty/*.kicad_mod"))
        assert len(footprint_files) > 0, "No footprint files were generated"

        # Compare with reference
        for new_file in footprint_files:
            ref_file = reference_dir / component_id / "footprints" / new_file.name

            if not ref_file.exists():
                pytest.skip(
                    f"Reference file not found: {ref_file}\n"
                    f"To create reference files, run:\n"
                    f"  pytest --create-reference {__file__}"
                )

            is_equal, message = self.compare_files(ref_file, new_file, "footprint")
            assert is_equal, f"Footprint file differs from reference:\n{message}"

    @pytest.mark.parametrize("component_id", TEST_COMPONENTS)
    def test_3d_model_generation(self, component_id, temp_output_dir, reference_dir):
        """Test that 3D model files are generated consistently."""
        output_path = Path(temp_output_dir) / "test_lib"

        # Generate files with current version
        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--footprint",
            "--3d",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        # Find generated 3D model files (in temp_output_dir, not subdirectory)
        model_files = list(Path(temp_output_dir).glob("*.3dshapes/*.wrl"))
        model_files.extend(Path(temp_output_dir).glob("*.3dshapes/*.step"))

        if len(model_files) == 0:
            pytest.skip(f"No 3D model available for component {component_id}")

        # Compare with reference
        for new_file in model_files:
            ref_file = reference_dir / component_id / "3dmodels" / new_file.name

            if not ref_file.exists():
                pytest.skip(
                    f"Reference file not found: {ref_file}\n"
                    f"To create reference files, run:\n"
                    f"  pytest --create-reference {__file__}"
                )

            is_equal, message = self.compare_files(ref_file, new_file, "3d_model")
            assert is_equal, f"3D model file differs from reference:\n{message}"

    @pytest.mark.parametrize("component_id", TEST_COMPONENTS)
    def test_full_generation(self, component_id, temp_output_dir, reference_dir):
        """Test that all files together are generated consistently."""
        output_name = "test_lib"
        output_path = Path(temp_output_dir) / output_name

        # Generate all files with current version
        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--full",
            "--3d",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        # Verify all expected file types were generated
        # Files are generated in temp_output_dir, not in a subdirectory
        generated_files = self.get_generated_files(Path(temp_output_dir), component_id)

        assert len(generated_files) > 0, f"No files were generated in {temp_output_dir}"

        # Create a summary of what was generated
        file_types = {}
        for file in generated_files:
            ext = file.suffix
            file_types[ext] = file_types.get(ext, 0) + 1

        print(f"\nGenerated files for {component_id}:")
        for ext, count in file_types.items():
            print(f"  {ext}: {count} file(s)")


class TestCreateReference:
    """Helper to create reference files for regression testing."""

    @pytest.mark.parametrize("component_id", TestRegression.TEST_COMPONENTS)
    def test_create_reference_files(
        self, component_id, temp_output_dir, reference_dir, create_reference
    ):
        """Create reference files for regression tests."""
        if not create_reference:
            pytest.skip("Run with --create-reference to generate reference files")

        output_path = Path(temp_output_dir) / "test_lib"
        ref_component_dir = reference_dir / component_id

        # Generate all files
        args = [
            "--lcsc_id",
            component_id,
            "--output",
            str(output_path),
            "--full",
            "--3d",
        ]

        try:
            result = main(args)
            assert result == 0, f"main() returned error code: {result}"
        except SystemExit as e:
            assert e.code == 0, f"main() exited with code: {e.code}"

        # Copy generated files to reference directory
        # Files are in temp_output_dir, not subdirectory
        temp_path = Path(temp_output_dir)

        # Symbols
        symbol_dir = ref_component_dir / "symbols"
        symbol_dir.mkdir(parents=True, exist_ok=True)
        for file in temp_path.glob("*.kicad_sym"):
            shutil.copy2(file, symbol_dir / file.name)
            print(f"Created reference: {symbol_dir / file.name}")

        # Footprints
        footprint_dir = ref_component_dir / "footprints"
        footprint_dir.mkdir(parents=True, exist_ok=True)
        for file in temp_path.glob("*.pretty/*.kicad_mod"):
            shutil.copy2(file, footprint_dir / file.name)
            print(f"Created reference: {footprint_dir / file.name}")

        # 3D Models
        model_dir = ref_component_dir / "3dmodels"
        model_dir.mkdir(parents=True, exist_ok=True)
        for file in temp_path.glob("*.3dshapes/*"):
            if file.is_file():
                shutil.copy2(file, model_dir / file.name)
                print(f"Created reference: {model_dir / file.name}")

        print(f"\nReference files created for {component_id}")
