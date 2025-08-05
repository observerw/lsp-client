FROM ubuntu:22.04
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/