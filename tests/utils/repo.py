from __future__ import annotations

import asyncio as aio
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path

import aiofiles
import httpx

logger = logging.getLogger(__name__)


async def run_command(
    *cmd: str,
    cwd: Path | None = None,
    error_msg: str = "",
) -> None:
    try:
        process = await aio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=aio.subprocess.PIPE,
            stderr=aio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            stderr_str = stderr.decode() if stderr else ""
            raise RuntimeError(
                f"{error_msg}: Command failed with return code {process.returncode}. stderr: {stderr_str}"
            )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Command '{cmd[0]}' is not installed or not available in PATH"
        ) from e


async def prepare_repo(repo_id: str, commit: str, save_path: Path) -> Path:
    """Download and init github repo from commit."""

    logger.debug("Preparing repo %s at commit %s", repo_id, commit)

    _, repo_name = repo_id.split("/", 1)
    # zipball folder format: <repo_id>-<commit_hash>
    repo_path = save_path / f"{repo_id.replace('/', '-')}-{commit[:7]}"
    if repo_path.exists():
        logger.debug("Repo %s already exists, skipping download", repo_path)
        return repo_path

    download_url = (
        f"https://ghfast.top/https://github.com/{repo_id}/archive/{commit}.zip"
    )

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        zip_file_path = Path(temp_dir) / f"{commit}.zip"

        async with (
            httpx.AsyncClient() as client,
            client.stream(
                "GET",
                download_url,
                follow_redirects=True,
                timeout=None,
            ) as response,
        ):
            response.raise_for_status()
            async with aiofiles.open(zip_file_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)

        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            await aio.to_thread(zip_ref.extractall, save_path)

    extract_path = save_path / f"{repo_name}-{commit}"
    shutil.move(extract_path, repo_path)

    logger.debug("Extracted repo to %s", repo_path)

    await run_command(
        "git",
        "init",
        cwd=repo_path,
        error_msg="Failed to initialize git repository",
    )
    await run_command(
        "git",
        "add",
        ".",
        cwd=repo_path,
        error_msg="Failed to add files to git repository",
    )
    await run_command(
        "git",
        "commit",
        "-m",
        "initial commit",
        cwd=repo_path,
        error_msg="Failed to commit changes",
    )

    logger.debug("Initialized git repository at %s", repo_path)

    return repo_path
