# Regression Tests

Tests to ensure generated files remain consistent across versions.

## Overview

`tests/reference_outputs/` contains the reference files used for comparison.
This folder is listed in `.gitignore` and **not tracked in the repository** to
keep the repo size small (~30 MB of `.step`, `.wrl`, `.kicad_mod`, `.kicad_sym` files).

If no reference files are present, regression tests **skip automatically**.

## Generate Reference Files

Required once before running regression tests:

```bash
pip install .[dev]
pytest tests/test_regression.py --create-reference -v
```

## Run Tests

```bash
pytest tests/ -v
```

## Update References

When output changes are intentional, regenerate all reference files:

```bash
rm -rf tests/reference_outputs/
pytest tests/test_regression.py --create-reference -v
```

## Storing Reference Files with Git LFS (optional)

If you want to track reference files in the repository, Git LFS is recommended
due to the large binary files.

**One-time setup (repository maintainer):**

```bash
git lfs install
git lfs track "tests/reference_outputs/**"
git add .gitattributes

pytest tests/test_regression.py --create-reference -v
git add tests/reference_outputs/
git commit -m "test: add regression reference files via Git LFS"
git push
```
