# PyPI Publishing Checklist

This document outlines the steps to publish `gcallm` to PyPI.

## Pre-Publication Checklist

### Code Quality
- [x] All tests passing (114/114 tests)
- [x] Code formatted with `black` and `ruff format`
- [x] Linting passes with `ruff check`
- [x] Type checking configured with `mypy`
- [x] No duplicate files (consolidated formatters)
- [x] Import statements organized

### Documentation
- [x] README.md is complete and accurate
- [x] Test count updated (114 tests)
- [x] Installation instructions included
- [x] Usage examples provided
- [x] Troubleshooting section included
- [x] LICENSE file present (MIT)

### Package Configuration
- [x] pyproject.toml properly configured
- [x] Version number set (0.1.0)
- [x] Dependencies listed correctly
- [x] Python version requirement specified (>=3.10)
- [x] Entry points configured (`gcallm` CLI)
- [x] Package metadata complete (description, keywords, classifiers)
- [x] Repository URLs included

### Additional Files
- [x] .gitignore present
- [x] CLAUDE.md with project instructions
- [x] Comprehensive test suite
- [x] Makefile for development workflows
- [x] Linting configuration (ruff.toml)

## Building for PyPI

### 1. Clean Previous Builds
```bash
make clean
# or manually:
rm -rf dist/ build/ *.egg-info
```

### 2. Build Distribution Packages
```bash
make build
# or manually:
python -m build
```

This creates:
- `dist/gcallm-0.1.0.tar.gz` (source distribution)
- `dist/gcallm-0.1.0-py3-none-any.whl` (wheel distribution)

### 3. Verify Build
```bash
# Check package contents
tar -tzf dist/gcallm-0.1.0.tar.gz

# Check wheel contents
unzip -l dist/gcallm-0.1.0-py3-none-any.whl
```

## Publishing to PyPI

### Option 1: Test PyPI (Recommended First)

Test your package on Test PyPI before publishing to production:

```bash
# Install twine if not already installed
pip install twine

# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ gcallm
```

### Option 2: Production PyPI

Once verified on Test PyPI:

```bash
make publish
# or manually:
python -m twine upload dist/*
```

You'll be prompted for your PyPI credentials:
- Username: `__token__`
- Password: Your PyPI API token

### Getting PyPI API Token

1. Create account at https://pypi.org/
2. Enable 2FA (required for API tokens)
3. Go to Account Settings → API Tokens
4. Create new token (scope: entire account or this project)
5. Save token securely (shown only once!)

## Post-Publication

### 1. Verify Installation
```bash
# Install from PyPI
pip install gcallm

# Verify it works
gcallm --help
```

### 2. Tag Release in Git
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### 3. Create GitHub Release
1. Go to https://github.com/WarrenZhu050413/gcallm/releases
2. Click "Draft a new release"
3. Select tag: `v0.1.0`
4. Add release notes (changelog)
5. Publish release

## Updating the Package

When releasing a new version:

1. Update version in `pyproject.toml`
2. Update CHANGELOG (if you have one)
3. Run tests: `make test`
4. Build: `make build`
5. Publish: `make publish`
6. Tag release in Git

## Common Issues

### "File already exists" error
- PyPI doesn't allow overwriting versions
- Increment version number in `pyproject.toml`
- Rebuild and republish

### Import errors after installation
- Check `pyproject.toml` dependencies
- Verify package structure (`gcallm/__init__.py` exists)
- Test with `pip install -e .` locally first

### Missing dependencies
- Ensure all dependencies in `pyproject.toml`
- Test in clean virtual environment
- Check Node.js requirement (for MCP server)

## Quality Gates Before Publishing

Run these commands to ensure quality:

```bash
# Format code
make format

# Run linter
make lint

# Run tests
make test

# Build package
make build

# Check distribution
twine check dist/*
```

All should pass before publishing!

## Resources

- PyPI: https://pypi.org/
- Test PyPI: https://test.pypi.org/
- Twine docs: https://twine.readthedocs.io/
- Python packaging guide: https://packaging.python.org/
