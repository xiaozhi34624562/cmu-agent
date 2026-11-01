"""Small deterministic tools used by the agent tests (course-provided; do
not edit).

``make_fixture_tools()`` returns a fresh ``FixtureTools`` each time:

    fx = make_fixture_tools()
    fx.tools            # list[ToolSpec], in the order of TOOL_NAMES
    fx.calls            # [(tool name, args dict), ...], one entry per time a
                        # tool function actually ran, in order
    fx.notes            # the texts passed to write_note, in order
    fx.spec("add")      # one ToolSpec by name
    fx.count("add")     # how many times add ran

Every schema lists its required arguments, gives each a type, and sets
``additionalProperties`` to false, so a call with a missing, mistyped, or
extra argument is invalid. All tools are read-only except ``write_note``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from cs329z_hw1.types import ToolSpec

TOOL_NAMES = ["echo", "add", "lookup", "fail", "slow", "big_output", "write_note"]

# The data behind the lookup tool.
DIRECTORY = {
    "hq_address": "4100 Alder Street, Houston, TX 77002",
    "it_helpdesk": "extension 4410",
    "payroll_cutoff": "the 25th of each month",
    "guest_wifi": "network CardinalGuest, password heron-47-maple",
    "parking_office": "Garage B, level 1, room 12",
}

FAIL_MESSAGE = "fixture tool failed on purpose (code 7341)"


def _object(properties: dict, required: list[str]) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


@dataclass
class FixtureTools:
    tools: list[ToolSpec] = field(default_factory=list)
    calls: list[tuple[str, dict]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def spec(self, name: str) -> ToolSpec:
        for tool in self.tools:
            if tool.name == name:
                return tool
        raise KeyError(name)

    def count(self, name: str) -> int:
        return sum(1 for called, _ in self.calls if called == name)


def make_fixture_tools() -> FixtureTools:
    """Fresh tool instances with empty call records."""
    fx = FixtureTools()

    def record(name: str, **args) -> None:
        fx.calls.append((name, args))

    def echo(text):
        record("echo", text=text)
        return text

    def add(a, b):
        record("add", a=a, b=b)
        return a + b

    def lookup(key):
        record("lookup", key=key)
        return DIRECTORY[key]

    def fail():
        record("fail")
        raise RuntimeError(FAIL_MESSAGE)

    def slow(seconds):
        record("slow", seconds=seconds)
        time.sleep(seconds)
        return f"waited {seconds} seconds"

    def big_output(n_lines):
        record("big_output", n_lines=n_lines)
        return "\n".join(f"line {i}: filler text for output number {i}" for i in range(1, n_lines + 1))

    def write_note(text):
        record("write_note", text=text)
        fx.notes.append(text)
        return f"saved note {len(fx.notes)}"

    fx.tools = [
        ToolSpec(
            name="echo",
            description="Return the given text unchanged.",
            parameters=_object(
                {"text": {"type": "string", "description": "The text to return."}}, ["text"]
            ),
            fn=echo,
            read_only=True,
        ),
        ToolSpec(
            name="add",
            description="Add two numbers and return their sum.",
            parameters=_object(
                {
                    "a": {"type": "number", "description": "The first number."},
                    "b": {"type": "number", "description": "The second number."},
                },
                ["a", "b"],
            ),
            fn=add,
            read_only=True,
        ),
        ToolSpec(
            name="lookup",
            description=(
                "Look up one entry in the office directory. The keys are: "
                "hq_address (street address of headquarters), it_helpdesk (phone "
                "extension of the IT helpdesk), payroll_cutoff (monthly payroll "
                "cutoff date), guest_wifi (guest network name and password), "
                "parking_office (location of the parking office)."
            ),
            parameters=_object(
                {
                    "key": {
                        "type": "string",
                        "enum": list(DIRECTORY),
                        "description": "The directory key to look up.",
                    }
                },
                ["key"],
            ),
            fn=lookup,
            read_only=True,
        ),
        ToolSpec(
            name="fail",
            description=(
                "Always raises an error. It exists to test error handling and "
                "takes no arguments."
            ),
            parameters=_object({}, []),
            fn=fail,
            read_only=True,
        ),
        ToolSpec(
            name="slow",
            description="Wait for the given number of seconds, then report how long it waited.",
            parameters=_object(
                {
                    "seconds": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 5,
                        "description": "How long to wait, in seconds (0 to 5).",
                    }
                },
                ["seconds"],
            ),
            fn=slow,
            read_only=True,
        ),
        ToolSpec(
            name="big_output",
            description="Return n_lines lines of numbered filler text, one line per number.",
            parameters=_object(
                {
                    "n_lines": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "How many lines to return.",
                    }
                },
                ["n_lines"],
            ),
            fn=big_output,
            read_only=True,
        ),
        ToolSpec(
            name="write_note",
            description="Save a text note to the notebook. This changes stored data.",
            parameters=_object(
                {"text": {"type": "string", "description": "The text of the note."}}, ["text"]
            ),
            fn=write_note,
            read_only=False,
        ),
    ]
    return fx
