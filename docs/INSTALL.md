# Installation Guide

## For Users

### Using pipx (Recommended)
```bash
pipx install hardlink-cleaner
```

### Using pip
```bash
pip install --user hardlink-cleaner
```

### From GitHub
```bash
pipx install git+https://github.com/wmp/hardlink-cleaner.git
```

### From Source
```bash
git clone https://github.com/wmp/hardlink-cleaner.git
cd hardlink-cleaner
pip install .
```

## For Developers

### Development Installation
```bash
git clone https://github.com/wmp/hardlink-cleaner.git
cd hardlink-cleaner
pip install -e .
```

### Running Without Installation
```bash
python3 hardlink_cleaner.py --help
```

### Building the Package
```bash
# Install build tools
pip install build

# Build
python3 -m build

# Output will be in dist/
ls dist/
```

### Testing Local Installation
```bash
# Create virtual environment
python3 -m venv test-env
source test-env/bin/activate

# Install from local wheel
pip install dist/hardlink_cleaner-1.0.0-py3-none-any.whl

# Test
hardlink-cleaner --help

# Cleanup
deactivate
rm -rf test-env
```

## Publishing to PyPI

### Setup
```bash
# Install twine
pip install twine

# Create PyPI account at https://pypi.org/account/register/
```

### Test on TestPyPI First
```bash
# Upload to TestPyPI
python3 -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pipx install --index-url https://test.pypi.org/simple/ hardlink-cleaner
```

### Publish to PyPI
```bash
# Build fresh
rm -rf dist/ build/ *.egg-info
python3 -m build

# Upload to PyPI
python3 -m twine upload dist/*

# Verify
pipx install hardlink-cleaner
```

### Using GitHub Actions (Optional)

Create `.github/workflows/publish.yml`:
```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Then create a PyPI API token and add it as `PYPI_API_TOKEN` secret in GitHub repository settings.

## Uninstalling

```bash
# If installed with pipx
pipx uninstall hardlink-cleaner

# If installed with pip
pip uninstall hardlink-cleaner
```
