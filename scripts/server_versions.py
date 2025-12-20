from __future__ import annotations

import json
import subprocess
import sys
import tomllib
import urllib.request


def get_latest_npm(package):
    with urllib.request.urlopen(
        f"https://registry.npmjs.org/{package}/latest"
    ) as response:
        return json.load(response)["version"]


def get_latest_pypi(package):
    with urllib.request.urlopen(f"https://pypi.org/pypi/{package}/json") as response:
        return json.load(response)["info"]["version"]


def get_latest_github_release(repo):
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/latest"
    )
    request.add_header("User-Agent", "lsp-client-updater")
    import os

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return json.load(response)["tag_name"]


def get_latest_custom(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main():
    with open("container/registry.toml", "rb") as f:
        wiki = tomllib.load(f)

    versions = {}
    for server, config in wiki.items():
        if not isinstance(config, dict):
            continue
        try:
            if config["type"] == "npm":
                versions[server] = get_latest_npm(config["package"])
            elif config["type"] == "pypi":
                versions[server] = get_latest_pypi(config["package"])
            elif config["type"] == "github":
                v = get_latest_github_release(config["repo"])
                if config.get("strip_v"):
                    v = v.lstrip("v")
                versions[server] = v
            elif config["type"] == "custom":
                versions[server] = get_latest_custom(config["command"])
        except Exception as e:
            print(f"Error fetching version for {server}: {e}", file=sys.stderr)
            continue

    print(json.dumps(versions, indent=2))


if __name__ == "__main__":
    main()
