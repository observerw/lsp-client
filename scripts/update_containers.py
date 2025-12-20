from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def update_container_file(server_name: str, version: str) -> bool:
    container_file = Path(f"container/{server_name}/ContainerFile")
    if not container_file.exists():
        print(f"ContainerFile for {server_name} not found at {container_file}")
        return False

    content = container_file.read_text()
    new_content = re.sub(r"ARG VERSION=.*", f"ARG VERSION={version}", content, count=1)

    if content != new_content:
        container_file.write_text(new_content)
        print(f"Updated {server_name} to {version}")
        return True

    return False


def main():
    # Capture the output of server_versions.py
    result = subprocess.run(
        [sys.executable, "scripts/server_versions.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    versions = json.loads(result.stdout)

    updated_servers = []
    for server, version in versions.items():
        if update_container_file(server, version):
            updated_servers.append(server)

    if updated_servers:
        print(f"Updated servers: {', '.join(updated_servers)}")
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"updated_servers={json.dumps(updated_servers)}\n")
                f.write("has_updates=true\n")
    else:
        print("No updates found.")
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("has_updates=false\n")


if __name__ == "__main__":
    main()
