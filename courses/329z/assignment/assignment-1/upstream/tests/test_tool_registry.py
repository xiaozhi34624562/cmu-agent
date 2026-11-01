"""Tests for problem (tool_registry). Deterministic: no model calls.

The registry is built with ``run_tool_registry`` from the fixture tools in
``tests/fixture_tools.py``. The tests use three of its methods: ``schemas()``,
``validate(name, args)`` (a ToolResult with status unknown_tool or
invalid_args, or None when the call could run; the tool is not called) and
``execute(name, args)``. Each fixture tool records every time its function
runs, so the tests can tell whether the registry executed a call.
"""

from __future__ import annotations

import pytest

from cs329z_hw1.types import ToolResult, ToolSpec
from cs329z_hw1 import adapters
from tests.fixture_tools import DIRECTORY, FAIL_MESSAGE, TOOL_NAMES, make_fixture_tools


def build():
    fx = make_fixture_tools()
    return adapters.run_tool_registry(fx.tools), fx


def execute(registry, name, args) -> ToolResult:
    """Call registry.execute and check the shape of what comes back."""
    try:
        result = registry.execute(name, args)
    except Exception as exc:
        pytest.fail(
            f"execute({name!r}, {args!r}) raised {type(exc).__name__}: {exc}. "
            "execute must return a ToolResult for every input and never raise.",
            pytrace=False,
        )
    assert isinstance(result, ToolResult), (
        f"execute({name!r}, {args!r}) must return a cs329z_hw1.types.ToolResult, "
        f"got {type(result).__name__}: {result!r}"
    )
    assert isinstance(result.content, str), (
        f"execute({name!r}, {args!r}): ToolResult.content must be a str, "
        f"got {type(result.content).__name__}"
    )
    return result


def expect_status(result: ToolResult, status: str, name, args) -> None:
    assert result.status == status, (
        f"execute({name!r}, {args!r}): expected status {status!r}, got "
        f"{result.status!r} with content {result.content!r}"
    )


# ------------------------------------------------------------- schemas ----


def test_schemas_lists_every_tool_in_registration_order():
    """schemas() returns one dict per tool, in the order the tools were given."""
    registry, fx = build()
    schemas = registry.schemas()
    assert isinstance(schemas, list), f"schemas() must return a list, got {type(schemas).__name__}"
    names = [s.get("name") if isinstance(s, dict) else s for s in schemas]
    assert names == TOOL_NAMES, (
        f"schemas() must list the tools in registration order {TOOL_NAMES}, got {names}"
    )


def test_schemas_entries_have_name_description_parameters_only():
    """Each entry has exactly the keys name, description, parameters, with the
    values from the ToolSpec. The function and read_only flag are not included."""
    registry, fx = build()
    for schema, spec in zip(registry.schemas(), fx.tools):
        assert set(schema) == {"name", "description", "parameters"}, (
            f"schema for {spec.name!r} must have exactly the keys name, description, "
            f"parameters; got {sorted(schema)}"
        )
        assert schema["description"] == spec.description, (
            f"schema for {spec.name!r}: description differs from the ToolSpec's"
        )
        assert schema["parameters"] == spec.parameters, (
            f"schema for {spec.name!r}: parameters differs from the ToolSpec's"
        )


def test_registration_order_follows_the_input_list():
    """A registry built from a reordered tool list reports that order."""
    fx = make_fixture_tools()
    tools = list(reversed(fx.tools))
    registry = adapters.run_tool_registry(tools)
    names = [s["name"] for s in registry.schemas()]
    assert names == [t.name for t in tools], (
        f"expected schemas() in the order the tools were registered "
        f"{[t.name for t in tools]}, got {names}"
    )


def test_empty_registry():
    """A registry with no tools has no schemas and reports unknown_tool."""
    registry = adapters.run_tool_registry([])
    assert registry.schemas() == [], f"expected [] from schemas(), got {registry.schemas()!r}"
    result = execute(registry, "echo", {"text": "hi"})
    expect_status(result, "unknown_tool", "echo", {"text": "hi"})


# ------------------------------------------------------------------ ok ----


def test_execute_ok_runs_the_tool_once_with_the_arguments():
    registry, fx = build()
    args = {"a": 17, "b": 25}
    result = execute(registry, "add", args)
    expect_status(result, "ok", "add", args)
    assert result.content == "42", f"add(17, 25): expected content '42', got {result.content!r}"
    assert fx.calls == [("add", {"a": 17, "b": 25})], (
        f"expected the add function to run once with a=17, b=25; recorded calls: {fx.calls}"
    )


@pytest.mark.parametrize(
    "name,args,expected",
    [
        ("echo", {"text": "hello\nworld"}, "hello\nworld"),
        ("add", {"a": 1.5, "b": 2}, "3.5"),
        ("lookup", {"key": "it_helpdesk"}, DIRECTORY["it_helpdesk"]),
        ("big_output", {"n_lines": 0}, ""),
        ("write_note", {"text": "first"}, "saved note 1"),
    ],
)
def test_execute_ok_content_is_str_of_return_value(name, args, expected):
    """On success, content is str(return value) of the tool function."""
    registry, fx = build()
    result = execute(registry, name, args)
    expect_status(result, "ok", name, args)
    assert result.content == expected, (
        f"execute({name!r}, {args!r}): expected content {expected!r} "
        f"(str of the tool's return value), got {result.content!r}"
    )


@pytest.mark.parametrize("value", [None, 12, 2.5, ["a", 1], {"k": "v"}, True])
def test_non_string_return_values_are_converted_with_str(value):
    spec = ToolSpec(
        name="constant",
        description="Return a fixed value.",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        fn=lambda: value,
        read_only=True,
    )
    registry = adapters.run_tool_registry([spec])
    result = execute(registry, "constant", {})
    expect_status(result, "ok", "constant", {})
    assert result.content == str(value), (
        f"the tool returned {value!r}; expected content {str(value)!r}, got {result.content!r}"
    )


def test_side_effects_happen_on_ok():
    registry, fx = build()
    execute(registry, "write_note", {"text": "one"})
    execute(registry, "write_note", {"text": "two"})
    assert fx.notes == ["one", "two"], (
        f"expected write_note to have saved ['one', 'two'], got {fx.notes}"
    )


# ------------------------------------------------------------ validate ----


def validate(registry, name, args):
    """Call registry.validate and check the shape of what comes back."""
    try:
        result = registry.validate(name, args)
    except Exception as exc:
        pytest.fail(
            f"validate({name!r}, {args!r}) raised {type(exc).__name__}: {exc}. "
            "validate must return a ToolResult or None and never raise.",
            pytrace=False,
        )
    assert result is None or isinstance(result, ToolResult), (
        f"validate({name!r}, {args!r}) must return None or a ToolResult, got {result!r}"
    )
    return result


def test_validate_accepts_a_good_call_without_running_it():
    """validate(name, args) returns None for a call that execute would run,
    and does not call the tool."""
    registry, fx = build()
    assert validate(registry, "echo", {"text": "hi"}) is None
    assert validate(registry, "add", {"a": 1, "b": 2}) is None
    assert fx.calls == [], f"validate must not run the tool; recorded calls: {fx.calls}"


def test_validate_rejects_an_unknown_tool():
    registry, fx = build()
    result = validate(registry, "no_such_tool", {"text": "hi"})
    assert result is not None and result.status == "unknown_tool", (
        f"validate of an unknown tool must return a ToolResult with status unknown_tool, got {result!r}"
    )
    assert result.content.strip()
    assert fx.calls == []


@pytest.mark.parametrize("name,args", [("add", {"a": 1}), ("echo", {"text": 5}), ("lookup", {"key": "not_a_key"})])
def test_validate_rejects_invalid_args(name, args):
    registry, fx = build()
    result = validate(registry, name, args)
    assert result is not None and result.status == "invalid_args", (
        f"validate({name!r}, {args!r}) must return a ToolResult with status invalid_args, got {result!r}"
    )
    assert result.content.strip()
    assert fx.calls == []


def test_validate_and_execute_agree():
    """execute rejects exactly the calls validate rejects, with the same status."""
    registry, fx = build()
    for name, args in [("echo", {"text": "hi"}), ("no_such_tool", {}), ("add", {"a": 1})]:
        checked = validate(registry, name, args)
        ran = execute(registry, name, args)
        if checked is None:
            assert ran.status == "ok", f"validate accepted {name}({args}) but execute returned {ran.status}"
        else:
            assert ran.status == checked.status, (
                f"validate returned {checked.status} for {name}({args}) but execute returned {ran.status}"
            )


# -------------------------------------------------------- unknown_tool ----


@pytest.mark.parametrize("name", ["no_such_tool", "", "Echo", "echo "])
def test_unknown_tool(name):
    """A name that is not registered (names are case-sensitive and compared
    exactly) gives status unknown_tool and runs nothing."""
    registry, fx = build()
    result = execute(registry, name, {"text": "hi"})
    expect_status(result, "unknown_tool", name, {"text": "hi"})
    assert result.content.strip(), "unknown_tool: content must describe the error, got an empty string"
    assert fx.calls == [], f"no tool function should run for an unknown tool; recorded calls: {fx.calls}"


# -------------------------------------------------------- invalid_args ----

INVALID_CASES = [
    pytest.param("add", {"a": 1}, id="missing-required"),
    pytest.param("add", {}, id="all-missing"),
    pytest.param("add", {"a": "1", "b": 2}, id="string-for-number"),
    pytest.param("echo", {"text": 5}, id="number-for-string"),
    pytest.param("big_output", {"n_lines": 2.5}, id="float-for-integer"),
    pytest.param("big_output", {"n_lines": "3"}, id="string-for-integer"),
    pytest.param("add", {"a": 1, "b": 2, "c": 3}, id="extra-argument"),
    pytest.param("fail", {"why": "x"}, id="extra-argument-no-params"),
    pytest.param("lookup", {"key": "not_a_key"}, id="value-not-in-enum"),
    pytest.param("slow", {"seconds": 60}, id="above-maximum"),
    pytest.param("echo", {"text": None}, id="null-for-string"),
]


@pytest.mark.parametrize("name,args", INVALID_CASES)
def test_invalid_args_are_rejected_without_running_the_tool(name, args):
    """Arguments that fail the tool's JSON Schema give status invalid_args, a
    non-empty content describing the problem, and the tool function is not
    called."""
    registry, fx = build()
    result = execute(registry, name, args)
    expect_status(result, "invalid_args", name, args)
    assert result.content.strip(), "invalid_args: content must describe the error, got an empty string"
    assert fx.calls == [], (
        f"execute({name!r}, {args!r}): the tool function must not run when the "
        f"arguments are invalid; recorded calls: {fx.calls}"
    )


def test_valid_call_after_invalid_call_still_works():
    registry, fx = build()
    execute(registry, "add", {"a": 1})
    result = execute(registry, "add", {"a": 1, "b": 2})
    expect_status(result, "ok", "add", {"a": 1, "b": 2})
    assert result.content == "3", f"expected content '3', got {result.content!r}"


# ---------------------------------------------------------- tool_error ----


def test_tool_that_raises_gives_tool_error_with_the_exception_message():
    """When the tool function raises, execute returns status tool_error and
    the content includes the exception's message."""
    registry, fx = build()
    result = execute(registry, "fail", {})
    expect_status(result, "tool_error", "fail", {})
    assert FAIL_MESSAGE in result.content, (
        f"the tool raised RuntimeError({FAIL_MESSAGE!r}); expected that message in "
        f"content, got {result.content!r}"
    )
    assert fx.count("fail") == 1, f"expected fail to run exactly once, ran {fx.count('fail')} times"


@pytest.mark.parametrize(
    "exc", [ValueError("bad value 9127"), KeyError("missing key 9127"), ZeroDivisionError("division 9127")]
)
def test_any_exception_type_is_contained(exc):
    def boom():
        raise exc

    spec = ToolSpec(
        name="boom",
        description="Raise an exception.",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        fn=boom,
        read_only=True,
    )
    registry = adapters.run_tool_registry([spec])
    result = execute(registry, "boom", {})
    expect_status(result, "tool_error", "boom", {})
    assert "9127" in result.content, (
        f"the tool raised {exc!r}; expected the exception's message in content, "
        f"got {result.content!r}"
    )


def test_registry_keeps_working_after_a_tool_error():
    registry, fx = build()
    execute(registry, "fail", {})
    result = execute(registry, "echo", {"text": "still here"})
    expect_status(result, "ok", "echo", {"text": "still here"})
    assert result.content == "still here", f"expected content 'still here', got {result.content!r}"
