from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal, final, override

from attrs import define, field
from loguru import logger
from pydantic import BaseModel, Field

from lsp_client.jsonrpc.parse import RawPackage

from .abc import LSPServer
from .local import LocalServer


class MountBase(BaseModel):
    type: str
    target: str
    source: str | None = None
    readonly: bool = False

    def _parts(self) -> list[str]:
        parts = [f"type={self.type}"]
        if self.source:
            parts.append(f"source={self.source}")
        parts.append(f"target={self.target}")
        if self.readonly:
            parts.append("readonly")
        return parts

    def __str__(self) -> str:
        return ",".join(self._parts())


class BindMount(MountBase):
    type: Literal["bind"] = "bind"

    bind_propagation: (
        Literal["private", "rprivate", "shared", "rshared", "slave", "rslave"] | None
    ) = None

    def _parts(self) -> list[str]:
        parts = super()._parts()
        if self.bind_propagation:
            parts.append(f"bind-propagation={self.bind_propagation}")

        return parts

    @classmethod
    def from_path(cls, path: Path) -> BindMount:
        absolute_path = path.resolve()

        if absolute_path.drive:
            raise ValueError(
                f"Path '{absolute_path}' contains a drive letter, which is not supported "
                "for same-path bind mounts in Linux containers. "
                "On Windows, you must explicitly separate 'source' and 'target' paths."
            )

        return cls(source=str(absolute_path), target=str(absolute_path))


class VolumeMount(MountBase):
    type: Literal["volume"] = "volume"

    volume_driver: str | None = None
    volume_subpath: str | None = None
    volume_nocopy: bool = False
    volume_opt: list[str] | None = None

    def _parts(self) -> list[str]:
        parts = super()._parts()

        if self.volume_driver:
            parts.append(f"volume-driver={self.volume_driver}")
        if self.volume_subpath:
            parts.append(f"volume-subpath={self.volume_subpath}")
        if self.volume_nocopy:
            parts.append("volume-nocopy")
        if self.volume_opt:
            for opt in self.volume_opt:
                parts.append(f"volume-opt={opt}")

        return parts


class TmpfsMount(MountBase):
    type: Literal["tmpfs"] = "tmpfs"

    tmpfs_size: int | None = None
    tmpfs_mode: int | None = None

    def _parts(self) -> list[str]:
        parts = super()._parts()

        if self.tmpfs_size is not None:
            parts.append(f"tmpfs-size={self.tmpfs_size}")
        if self.tmpfs_mode is not None:
            parts.append(f"tmpfs-mode={oct(self.tmpfs_mode)}")

        return parts


MountPoint = Annotated[
    BindMount | VolumeMount | TmpfsMount,
    Field(discriminator="type"),
]

Mount = MountPoint | str | Path


def _format_mount(mount: Mount) -> str:
    if isinstance(mount, Path):
        mount = BindMount.from_path(mount)

    return str(mount)


@final
@define
class ContainerServer(LSPServer):
    """Runtime for container backend, e.g. `docker` or `podman`."""

    image: str
    mounts: list[Mount]

    backend: Literal["docker", "podman"] = "docker"
    container_name: str | None = None
    extra_container_args: list[str] | None = None

    _local: LocalServer = field(init=False)

    def format_command(self) -> list[str]:
        cmd = [self.backend, "run", "--rm", "-i"]

        if self.container_name:
            cmd.extend(("--name", self.container_name))

        for mount in self.mounts:
            cmd.extend(("--mount", _format_mount(mount)))

        if self.extra_container_args:
            cmd.extend(self.extra_container_args)

        cmd.append(self.image)

        return cmd

    @override
    async def send(self, package: RawPackage) -> None:
        await self._local.send(package)

    @override
    async def receive(self) -> RawPackage | None:
        return await self._local.receive()

    @override
    async def kill(self) -> None:
        await self._local.kill()

    @override
    @asynccontextmanager
    async def run_process(self) -> AsyncGenerator[None]:
        command = self.format_command()
        logger.debug("Running docker runtime with command: {}", command)

        self._local = LocalServer(command=command)
        async with self._local.run_process():
            yield
