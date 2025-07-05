default:
    @just --list

clean:
    rm -rf dist/ build/ *.egg-info/
    find . -type d -name __pycache__ -delete
    find . -type f -name "*.pyc" -delete

build: clean
    uv build

bump-patch:
    uv run bump-my-version bump patch --verbose

bump-minor:
    uv run bump-my-version bump minor --verbose

bump-major:
    uv run bump-my-version bump major --verbose

release-patch: bump-patch
    #!/usr/bin/env bash
    VERSION=$(grep 'version = ' pyproject.toml | sed 's/.*version = "\(.*\)".*/\1/')
    git add pyproject.toml
    git commit -m "Bump version to $VERSION"
    git tag "v$VERSION"
    git push origin main
    git push origin "v$VERSION"
    @echo "✅ Version v$VERSION pushed, GitHub Actions will auto-release"

release-minor: bump-minor
    #!/usr/bin/env bash
    VERSION=$(grep 'version = ' pyproject.toml | sed 's/.*version = "\(.*\)".*/\1/')
    git add pyproject.toml
    git commit -m "Bump version to $VERSION"
    git tag "v$VERSION"
    git push origin main
    git push origin "v$VERSION"
    @echo "✅ Version v$VERSION pushed, GitHub Actions will auto-release"

release-major: bump-major
    #!/usr/bin/env bash
    VERSION=$(grep 'version = ' pyproject.toml | sed 's/.*version = "\(.*\)".*/\1/')
    git add pyproject.toml
    git commit -m "Bump version to $VERSION"
    git tag "v$VERSION"
    git push origin main
    git push origin "v$VERSION"
    @echo "✅ Version v$VERSION pushed, GitHub Actions will auto-release"
