# Publishing a Python Package to PyPI

A comprehensive guide to publishing Python packages to the Python Package Index (PyPI).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Configuration Files](#configuration-files)
4. [Building Your Package](#building-your-package)
5. [Testing Locally](#testing-locally)
6. [PyPI Authentication](#pypi-authentication)
7. [Publishing to TestPyPI (Optional)](#publishing-to-testpypi-optional)
8. [Publishing to PyPI](#publishing-to-pypi)
9. [Verification](#verification)
10. [Version Management](#version-management)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before publishing to PyPI, ensure you have:

- Python 3.10 or higher installed
- A PyPI account (create one at https://pypi.org/account/register/)
- `uv` package manager installed (recommended) or `pip` with `build` and `twine`

Install `uv` if you haven't:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Project Structure

A typical Python package structure looks like this:

```
your-package/
├── your_package/           # Main package directory
│   ├── __init__.py        # Makes it a package
│   ├── cli.py             # CLI entry point (if applicable)
│   └── other_modules.py   # Your package code
├── tests/                 # Test directory
│   └── test_*.py
├── pyproject.toml         # Project configuration (modern approach)
├── README.md              # Package documentation
├── LICENSE                # License file
├── .gitignore            # Git ignore rules
└── Makefile              # Build automation (optional)
```

## Configuration Files

### 1. `pyproject.toml` (Required)

This is the modern way to configure Python packages. Here's a complete example:

```toml
[project]
name = "your-package-name"
version = "0.1.0"
description = "A short description of your package"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
keywords = ["keyword1", "keyword2", "keyword3"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    # Add your runtime dependencies here
]

[project.urls]
Homepage = "https://github.com/yourusername/your-package"
Documentation = "https://github.com/yourusername/your-package#readme"
Repository = "https://github.com/yourusername/your-package"
Issues = "https://github.com/yourusername/your-package/issues"

[project.scripts]
# Define CLI entry points
your-command = "your_package.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

### 2. `README.md` (Required)

Your README will be displayed on PyPI. Include:
- Package description
- Installation instructions
- Quick start guide
- Usage examples
- Links to documentation

### 3. `LICENSE` (Recommended)

Choose a license for your package. Common choices:
- MIT License (permissive)
- Apache 2.0 (permissive with patent grant)
- GPL (copyleft)

### 4. `__init__.py`

Include version information in your package's `__init__.py`:

```python
"""Your package description."""

__version__ = "0.1.0"
```

## Building Your Package

### Using `uv` (Recommended)

```bash
# Build the package
uv build
```

This creates two files in the `dist/` directory:
- `your_package-0.1.0.tar.gz` (source distribution)
- `your_package-0.1.0-py3-none-any.whl` (wheel distribution)

### Using Traditional Tools

```bash
# Install build tools
pip install build

# Build the package
python -m build
```

## Testing Locally

Before publishing, test your package locally:

```bash
# Install in editable mode for development
uv tool install --editable .

# Or with pip
pip install -e .

# Run your CLI or import your package
your-command --help

# Run tests
pytest tests/
```

## PyPI Authentication

You need to authenticate with PyPI. There are two methods:

### Method 1: API Token (Recommended)

1. Go to https://pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Give it a name and scope (entire account or specific project)
5. Copy the token (starts with `pypi-`)

Configure your token:

```bash
# For uv
export UV_PUBLISH_TOKEN="pypi-your-token-here"

# Or create a ~/.pypirc file
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-your-token-here
EOF

chmod 600 ~/.pypirc
```

### Method 2: Username and Password (Less Secure)

Create `~/.pypirc`:
```ini
[pypi]
username = your_username
password = your_password
```

**Security Note**: Use API tokens when possible. Never commit credentials to git.

## Publishing to TestPyPI (Optional)

TestPyPI is a separate instance for testing. Highly recommended before publishing to the real PyPI.

1. Create an account at https://test.pypi.org/account/register/
2. Generate an API token
3. Publish to TestPyPI:

```bash
# With uv
UV_PUBLISH_TOKEN="pypi-test-token" uv publish --publish-url https://test.pypi.org/legacy/

# With twine
pip install twine
twine upload --repository testpypi dist/*
```

4. Test installation:

```bash
pip install --index-url https://test.pypi.org/simple/ your-package-name
```

## Publishing to PyPI

Once you've tested everything:

### Using `uv`

```bash
# Make sure you have a clean build
rm -rf dist/
uv build

# Publish (with token in environment)
export UV_PUBLISH_TOKEN="pypi-your-token-here"
uv publish

# Or publish directly (will prompt for credentials)
uv publish
```

### Using `twine`

```bash
# Build
python -m build

# Upload
twine upload dist/*
```

### Using a Makefile

Create convenient shortcuts in a `Makefile`:

```makefile
.PHONY: build publish clean

build: clean
	@echo "Building package..."
	uv build
	@echo "Package built! Files in dist/"

publish: build
	@echo "Publishing to PyPI..."
	@echo "Make sure you have PyPI credentials configured!"
	uv publish
	@echo "Published to PyPI!"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
```

Then simply run:
```bash
make publish
```

## Verification

After publishing, verify your package:

1. Check the PyPI page: `https://pypi.org/project/your-package-name/`
2. Install in a fresh environment:
   ```bash
   pip install your-package-name
   ```
3. Test the installation:
   ```bash
   your-command --version
   ```

## Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Updating Versions

When releasing a new version:

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. Update version in `__init__.py`:
   ```python
   __version__ = "0.2.0"
   ```

3. Create a git tag:
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

4. Build and publish:
   ```bash
   make publish
   # or
   uv build && uv publish
   ```

### Automated Version Management

Consider using tools like:
- `bump2version` or `bumpver` for version bumping
- GitHub Actions for automated releases
- `setuptools-scm` for git-based versioning

## Troubleshooting

### Common Issues

**1. "File already exists" error**
- You can't upload the same version twice
- Increment the version number in `pyproject.toml`
- Never delete and re-upload the same version

**2. Authentication failures**
- Verify your API token is correct
- Check token hasn't expired
- Ensure `~/.pypirc` has correct permissions (600)
- Try `rm ~/.pypirc` and reconfigure

**3. Module not found after installation**
- Check your package structure has `__init__.py`
- Verify the package name matches in `pyproject.toml`
- Ensure dependencies are listed correctly

**4. Import errors**
- Check `requires-python` version matches your code
- Verify all dependencies are in `pyproject.toml`
- Test in a fresh virtual environment

**5. README not showing on PyPI**
- Ensure `readme = "README.md"` is in `pyproject.toml`
- Verify README uses valid Markdown
- Check README file exists at build time

### Best Practices

1. **Always test locally first** with `pip install -e .`
2. **Use TestPyPI** before publishing to real PyPI
3. **Write comprehensive tests** - run them before publishing
4. **Keep dependencies minimal** - only include what's necessary
5. **Pin major versions** of dependencies (e.g., `>=1.0.0,<2.0.0`)
6. **Write good documentation** - your README is crucial
7. **Use semantic versioning** - follow the standard
8. **Tag releases in git** - makes tracking versions easier
9. **Never commit credentials** - use environment variables or `.pypirc`
10. **Check package size** - exclude unnecessary files with `.gitignore` and build config

### Useful Commands

```bash
# Check what will be included in your package
uv build --check

# List installed packages
pip list

# Show package information
pip show your-package-name

# Uninstall
pip uninstall your-package-name

# Force reinstall (for testing updates)
pip install --force-reinstall --no-cache-dir your-package-name
```

---

## Additional Resources

- [PyPI Official Documentation](https://packaging.python.org/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
- [PEP 621 - pyproject.toml spec](https://peps.python.org/pep-0621/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [TestPyPI](https://test.pypi.org/)
- [Semantic Versioning](https://semver.org/)

## Quick Reference: Publishing Checklist

- [ ] Update version in `pyproject.toml` and `__init__.py`
- [ ] Update `README.md` with changes
- [ ] Run tests: `pytest tests/`
- [ ] Clean previous builds: `make clean` or `rm -rf dist/`
- [ ] Build package: `uv build`
- [ ] Test locally: `pip install dist/*.whl`
- [ ] (Optional) Publish to TestPyPI first
- [ ] Set PyPI token: `export UV_PUBLISH_TOKEN="pypi-..."`
- [ ] Publish: `uv publish`
- [ ] Create git tag: `git tag -a v0.1.0 -m "Release 0.1.0"`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] Verify on PyPI: https://pypi.org/project/your-package/
- [ ] Test installation: `pip install your-package-name`

---

Happy publishing! 🚀
