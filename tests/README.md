# Regression Tests

Tests to ensure generated files remain consistent across versions.

## Setup

Create reference files first:

```bash
pip install pytest
pytest tests/test_regression.py --create-reference -v
```

## Run Tests

```bash
pytest tests/test_regression.py -v
```

## Update References

When output changes are intentional:

```bash
rm -rf tests/reference_outputs/
pytest tests/test_regression.py --create-reference -v
```

## Storing Reference Files with Git LFS (optional)

`tests/reference_outputs/` is listed in `.gitignore` and not tracked by default.
If you want to store the reference files in the repository, Git LFS is recommended
because the folder contains large binary files (`.step`, `.wrl`).

**One-time setup (repository maintainer):**

```bash
# Install Git LFS
git lfs install

# Track the reference output files
git lfs track "tests/reference_outputs/**"
git add .gitattributes

# Generate and add reference files
pytest tests/test_regression.py --create-reference -v
git add tests/reference_outputs/
git commit -m "test: add regression reference files via Git LFS"
git push
```

**For contributors** — generate reference files locally without committing:

```bash
pytest tests/test_regression.py --create-reference -v
# Files are gitignored and stay local only
```
