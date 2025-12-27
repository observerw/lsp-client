# Release Process

This repository uses automated release management with GitHub Actions.

## Creating a Release

To create a new release:

1. **Update the version** in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. **Commit and push** your changes:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 0.2.0"
   git push
   ```

3. **Create and push a version tag**:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. **Automatic actions**:
   - The `release.yml` workflow will automatically create a GitHub release with auto-generated release notes
   - The `publish.yml` workflow will trigger and publish the package to PyPI

## Release Notes

Release notes are automatically generated based on:
- Pull request titles and descriptions since the last release
- Labels applied to pull requests (see `.github/release.yml` for categories)

### PR Labels for Release Notes

Label your pull requests to categorize them in release notes:

- `feature`, `enhancement` → 🚀 Features
- `bug`, `fix` → 🐛 Bug Fixes  
- `documentation`, `docs` → 📚 Documentation
- `chore`, `maintenance`, `refactor` → 🧹 Maintenance
- Unlabeled PRs → 🔧 Other Changes

### Excluding from Release Notes

To exclude a PR from release notes, add one of these labels:
- `ignore-for-release`
- `dependencies`

## Manual Release (Alternative)

If you prefer to create releases manually:

1. Go to the [Releases page](https://github.com/lsp-client/python-sdk/releases)
2. Click "Draft a new release"
3. Choose or create a tag (e.g., `v0.2.0`)
4. Click "Generate release notes" to auto-generate notes
5. Review and edit as needed
6. Click "Publish release"

The `publish.yml` workflow will still trigger automatically to publish to PyPI.
