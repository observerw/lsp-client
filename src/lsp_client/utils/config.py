from __future__ import annotations

import fnmatch
from copy import deepcopy
from typing import Any

from attrs import define, field
from loguru import logger

from lsp_client.utils.uri import from_local_uri


def deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge two dictionaries.
    """
    result = deepcopy(base)
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


@define
class ConfigurationMap:
    """
    A helper class to manage LSP configuration.
    Supports global configuration and scope-specific overrides.
    """

    _global_config: dict[str, Any] = field(factory=dict)
    _scoped_configs: list[tuple[str, dict[str, Any]]] = field(factory=list)

    def add_scope(self, pattern: str, config: dict[str, Any]) -> None:
        """
        Add a configuration override for a specific file pattern.

        :param pattern: Glob pattern (e.g. "**/tests/**", "*.py")
        :param config: The configuration dict to merge for this scope
        """
        self._scoped_configs.append((pattern, config))

    def _get_section(self, config: Any, section: str | None) -> Any:
        if not section:
            return config

        # Traverse the config dictionary using the section path (e.g. "python.analysis")
        current = config
        for part in section.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def get(self, scope_uri: str | None, section: str | None) -> Any:
        # Start with global config
        final_config = self._global_config

        # If we have a scope, merge matching scoped configs
        if scope_uri:
            try:
                path_str = str(from_local_uri(scope_uri))
                for pattern, scoped_config in self._scoped_configs:
                    if fnmatch.fnmatch(path_str, pattern):
                        final_config = deep_merge(final_config, scoped_config)
            except Exception:
                logger.warning(f"Failed to parse scope URI: {scope_uri}")

        return self._get_section(final_config, section)
