"""Course-provided definition of the Cardinal toolset.

``CARDINAL_TOOLS`` fixes, for each of the ten tools your agent offers, its
name, the JSON Schema of its arguments, and whether it is read-only. The
tests and the simulated users rely on these names and argument names, so do
not change them. You may register additional tools of your own.

Two things are left to you: the implementation of each tool, and its
description (the text the model reads to decide when and how to call it).
``cardinal_spec`` combines the two with the fixed parts into a ``ToolSpec``:

    spec = cardinal_spec("search_docs", "Search the ... (your text)", my_search_docs)
"""

from __future__ import annotations

import copy
from typing import Any, Callable

from cs329z_hw1.types import ToolSpec


def _schema(properties: dict, required: list[str]) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


_STRING = {"type": "string"}
_K = {"type": "integer", "minimum": 1, "default": 5}

# name -> {"parameters": JSON Schema, "read_only": bool}, in a fixed order.
# A tool that is not read-only needs the user's approval in confirm mode.
# ``remember`` writes only to the agent's own memory store, so it is marked
# read-only and does not need approval.
CARDINAL_TOOLS: dict[str, dict[str, Any]] = {
    "search_emails": {
        "parameters": _schema({"query": _STRING, "k": _K}, ["query"]),
        "read_only": True,
    },
    "read_email": {
        "parameters": _schema({"email_id": _STRING}, ["email_id"]),
        "read_only": True,
    },
    "email_qa": {
        "parameters": _schema({"question": _STRING}, ["question"]),
        "read_only": True,
    },
    "daily_digest": {
        "parameters": _schema(
            {"date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}}, ["date"]
        ),
        "read_only": True,
    },
    "search_docs": {
        "parameters": _schema({"query": _STRING, "k": _K}, ["query"]),
        "read_only": True,
    },
    "read_doc": {
        "parameters": _schema(
            {"doc_id": _STRING, "start_line": {"type": "integer", "minimum": 1, "default": 1}},
            ["doc_id"],
        ),
        "read_only": True,
    },
    "run_terminal": {
        "parameters": _schema({"cmd": _STRING}, ["cmd"]),
        "read_only": False,
    },
    "remember": {
        "parameters": _schema({"fact": _STRING}, ["fact"]),
        "read_only": True,
    },
    "recall": {
        "parameters": _schema({"query": _STRING}, ["query"]),
        "read_only": True,
    },
    "ask_user": {
        "parameters": _schema({"question": _STRING}, ["question"]),
        "read_only": True,
    },
}


def cardinal_spec(name: str, description: str, fn: Callable[..., Any]) -> ToolSpec:
    """Build the ``ToolSpec`` for the Cardinal tool called ``name``.

    ``description`` and ``fn`` are yours. The parameter schema and the
    read-only flag come from ``CARDINAL_TOOLS``. ``fn`` is called with the
    arguments as keyword arguments, for example ``fn(query="...", k=3)``.
    Optional arguments the model leaves out are not filled in, so give them
    default values in ``fn``'s signature (k=5, start_line=1).
    """
    if name not in CARDINAL_TOOLS:
        raise KeyError(f"{name!r} is not a Cardinal tool. Known tools: {', '.join(CARDINAL_TOOLS)}")
    entry = CARDINAL_TOOLS[name]
    return ToolSpec(
        name=name,
        description=description,
        parameters=copy.deepcopy(entry["parameters"]),
        fn=fn,
        read_only=entry["read_only"],
    )
