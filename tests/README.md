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
