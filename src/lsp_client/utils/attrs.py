from __future__ import annotations

from functools import reduce
from typing import Any

import attrs


def can_merge_attrs(a: attrs.AttrsInstance, b: attrs.AttrsInstance) -> bool:
    """
    Check if two attrs instances can be merged.

    Rules:

    - Both instances must be attrs instances.
    - Both instances must be of the same type.
    """

    type_a = type(a)
    type_b = type(b)

    return all(
        (
            attrs.has(type_a),
            attrs.has(type_b),
            type_a is type_b,
        )
    )


def attrs_merge(base: Any | None, update: Any | None) -> Any:
    """
    Merge `update` attrs instance into `base` attrs instance.

    Merge rules:

    - non-None value overrides None value
    - Merge attrs instances of the same type recursively
    - otherwise, `update` value overrides `base` value
    """

    match base, update:
        case None, None:
            return None
        case base_value, None:
            return base_value
        case None, update_value:
            return update_value
        case base_value, update_value if can_merge_attrs(base_value, update_value):
            return attrs.evolve(
                base,
                **{
                    k: attrs_merge(getattr(base, k, None), v)
                    for k, v in attrs.asdict(update, recurse=False).items()
                },
            )
        # `update` takes precedence
        case _, update_value:
            return update_value


def attrs_merges(*args: Any) -> Any:
    """Merge multiple attrs instances into one."""

    return reduce(attrs_merge, args)
