bump version:
    # replace the version in pyproject.toml
    sed -i '' 's/version = ".*"/version = "{{ version }}"/'
    # commit the change
    git add pyproject.toml
    git commit -m "bump version to {{ version }}"
    # tag the commit
    git tag -a "v{{ version }}" -m "version {{ version }}"
    # push the commit and tag
    git push origin main
    git push origin "v{{ version }}"
    echo "Version bumped to {{ version }} and pushed to remote."