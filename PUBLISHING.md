# Publishing to PyPI

This guide explains how to publish the `plugah` package to PyPI.

## Automated Publishing (Recommended)

### Via GitHub Release

1. Create a new release on GitHub:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. Go to [GitHub Releases](https://github.com/cheesejaguar/plugah/releases)
3. Click "Create a new release"
4. Select the tag you just created
5. Add release notes
6. Click "Publish release"

The GitHub Action will automatically:
- Build the package
- Run tests on multiple Python versions
- Publish to PyPI
- Build and push Docker image

### Via Manual Workflow

1. Go to [Actions tab](https://github.com/cheesejaguar/plugah/actions)
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Choose to publish to Test PyPI or PyPI

## Manual Publishing

### Prerequisites

1. Install build tools:
   ```bash
   uv pip install --upgrade build twine
   ```

2. Configure PyPI credentials (one of):
   - Use API token (recommended):
     ```bash
     export TWINE_USERNAME=__token__
     export TWINE_PASSWORD=pypi-YOUR-TOKEN-HERE
     ```
   - Or create `~/.pypirc` (see `.pypirc.example`)

### Build the Package

1. Clean previous builds:
   ```bash
   rm -rf dist/ build/ *.egg-info
   ```

2. Build the distribution:
   ```bash
   python -m build
   ```

3. Check the build:
   ```bash
   twine check dist/*
   ls -la dist/
   ```

### Publish to Test PyPI (Optional)

1. Upload to Test PyPI:
   ```bash
   twine upload --repository testpypi dist/*
   ```

2. Test installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ plugah
   ```

### Publish to PyPI

1. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

2. Verify installation:
   ```bash
   pip install plugah
   ```

## Setting up Trusted Publishing

For GitHub Actions to publish without tokens:

1. Go to [PyPI account settings](https://pypi.org/manage/account/)
2. Navigate to "Publishing"
3. Add a new trusted publisher:
   - Owner: `cheesejaguar`
   - Repository: `plugah`
   - Workflow: `publish.yml`
   - Environment: `pypi`

4. Repeat for Test PyPI with environment `test-pypi`

## Version Management

1. Update version in:
   - `pyproject.toml`
   - `plugah/__init__.py`

2. Commit changes:
   ```bash
   git add -A
   git commit -m "chore: bump version to 0.1.0"
   ```

3. Create tag:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin main --tags
   ```

## Docker Publishing

Docker images are automatically built and pushed to GitHub Container Registry:

```bash
docker pull ghcr.io/cheesejaguar/plugah:latest
docker pull ghcr.io/cheesejaguar/plugah:0.1.0
```

## Troubleshooting

### Build Errors

- Ensure `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Check Python version: `python --version` (requires 3.9+)
- Clear caches: `rm -rf .cache __pycache__ *.egg-info`

### Upload Errors

- Check credentials: `twine check dist/*`
- Verify package name is available on PyPI
- Ensure version number is incremented
- Check network connectivity

### Installation Errors

- Clear pip cache: `pip cache purge`
- Use fresh virtual environment
- Check dependency conflicts: `pip check`

## Release Checklist

- [ ] All tests passing
- [ ] Version bumped in pyproject.toml and __init__.py
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] Create git tag
- [ ] Push tag to GitHub
- [ ] Verify GitHub Action completed
- [ ] Test installation from PyPI
- [ ] Announce release