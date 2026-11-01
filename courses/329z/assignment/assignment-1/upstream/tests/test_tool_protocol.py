"""Tests for problem (tool_protocol).

The tests never look at your call format. They write calls with
``run_format_tool_call``, read them with ``run_parse_response``, and check
what comes back. The live test sends ``run_render_tools`` output to the model
and checks the calls the model writes.
"""

from __future__ import annotations

import json

import jsonschema
import pytest

from cs329z_hw1.types import ParsedResponse, ToolCall
from cs329z_hw1 import adapters
from tests.conftest import eval_slice
from tests.fixture_tools import TOOL_NAMES, make_fixture_tools
from tests.helpers import load_fixture
from tests.thresholds import TOOL_PROTOCOL_MIN_CORRECT


def parse(reply: str) -> ParsedResponse:
    """Call run_parse_response and check the shape of what comes back."""
    try:
        parsed = adapters.run_parse_response(reply)
    except NotImplementedError:
        raise
    except Exception as exc:
        pytest.fail(
            f"run_parse_response raised {type(exc).__name__}: {exc}\n"
            f"It must never raise; report problems in ParsedResponse.error.\n"
            f"The reply was:\n{reply!r}",
            pytrace=False,
        )
    assert isinstance(parsed, ParsedResponse), (
        f"run_parse_response must return a cs329z_hw1.types.ParsedResponse, "
        f"got {type(parsed).__name__}"
    )
    if parsed.error is not None:
        assert parsed.tool_call is None, (
            f"when error is set, tool_call must be None. error={parsed.error!r}, "
            f"tool_call={parsed.tool_call!r}\nThe reply was:\n{reply!r}"
        )
    return parsed


def same_json(a, b) -> bool:
    """Equality that also compares JSON types, so 1, 1.0, True and "1" differ."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def assert_same_call(parsed: ParsedResponse, call: ToolCall, reply: str) -> None:
    assert parsed.error is None, (
        f"expected no error when parsing a reply written by run_format_tool_call, "
        f"got error={parsed.error!r}\nThe reply was:\n{reply!r}"
    )
    assert parsed.tool_call is not None, (
        f"expected a call to {call.name!r}, but tool_call is None.\nThe reply was:\n{reply!r}"
    )
    assert parsed.tool_call.name == call.name, (
        f"expected tool name {call.name!r}, got {parsed.tool_call.name!r}.\n"
        f"The reply was:\n{reply!r}"
    )
    assert same_json(parsed.tool_call.args, call.args), (
        f"the parsed args differ from the args that were formatted.\n"
        f"expected: {call.args!r}\n"
        f"got:      {parsed.tool_call.args!r}\n"
        f"The reply was:\n{reply!r}"
    )


# ---------------------------------------------------------- round trip ----

LONG = "The quarterly maintenance report lists every pump station by region. " * 8

ROUND_TRIP_CASES = [
    pytest.param("Adding the two numbers.", "add", {"a": 17, "b": 25}, id="simple"),
    pytest.param("", "add", {"a": 17, "b": 25}, id="empty-text"),
    pytest.param("Calling the tool with no arguments.", "fail", {}, id="empty-args"),
    pytest.param("", "fail", {}, id="empty-text-empty-args"),
    pytest.param("  \n Padded text.\n\n ", "echo", {"text": "x"}, id="text-is-stripped"),
    pytest.param(
        "First I will look this up.\nThen I will add the numbers.\n\nIt's the user's \"total\": 3 items.",
        "lookup",
        {"key": "it_helpdesk"},
        id="multi-line-text",
    ),
    pytest.param(
        "Nested values.",
        "make_report",
        {
            "filters": {"year": 2001, "tags": ["gas", "power"], "region": {"name": "west", "ids": [1, 2, 3]}},
            "limit": 10,
            "ratio": 0.25,
            "negative": -3,
            "verbose": True,
            "quiet": False,
            "cursor": None,
            "empty_list": [],
            "empty_object": {},
        },
        id="nested-args",
    ),
    pytest.param(
        "Types must survive.",
        "echo",
        {"a": "123", "b": "true", "c": "null", "d": "", "e": "  spaces kept  ", "f": 1, "g": 1.5, "h": "1.5"},
        id="strings-that-look-like-other-types",
    ),
    pytest.param(
        "Unicode.",
        "echo",
        {"text": "café, naïve, Zürich, 日本語, Ελληνικά, 😀, em dash —, curly quotes “ ”"},
        id="unicode",
    ),
    pytest.param(
        "Quotes and escapes.",
        "echo",
        {"text": "She said \"no\", then 'maybe'.\nSecond line.\n\tTabbed line.\r\nPath C:\\temp\\new and a lone backslash \\"},
        id="quotes-newlines-backslashes",
    ),
    pytest.param(
        "Braces and backticks.",
        "echo",
        {"text": "```python\nd = {\"k\": [1, 2, {\"x\": \"}\"}]}\nprint(f\"{d}\")\n```\nand `inline` and }}{{ and ]["},
        id="braces-brackets-backticks",
    ),
    pytest.param(
        "Markup characters.",
        "echo",
        {"text": "<b>bold</b> </div> <!-- c --> a < b > c & d; x=\"1\" 100% #tag @name $5 ~ ^ | : ="},
        id="angle-brackets-and-punctuation",
    ),
    pytest.param(
        "A shell command.",
        "run_terminal",
        {"cmd": "python3 -c 'import json; print(json.dumps({\"n\": len(open(\"emails.jsonl\").readlines())}))' | head -n 5"},
        id="shell-command",
    ),
    pytest.param("A long argument.", "write_note", {"text": LONG}, id="long-argument"),
]


@pytest.mark.parametrize("text,name,args", ROUND_TRIP_CASES)
def test_round_trip(text, name, args):
    """run_parse_response(run_format_tool_call(text, call)) gives back the
    call's name and args exactly, no error, and text equal to text.strip()."""
    call = ToolCall(name=name, args=args)
    reply = adapters.run_format_tool_call(text, call)
    assert isinstance(reply, str) and reply.strip(), (
        f"run_format_tool_call must return a non-empty str, got {reply!r}"
    )
    parsed = parse(reply)
    assert_same_call(parsed, call, reply)
    assert parsed.text == text.strip(), (
        f"expected ParsedResponse.text == {text.strip()!r}, got {parsed.text!r}.\n"
        f"The reply was:\n{reply!r}"
    )


def test_round_trip_when_an_argument_contains_a_formatted_call():
    """An argument value may itself contain text in your call format (for
    example a note that quotes an earlier reply). The outer call must still
    parse to exactly one call with that argument intact."""
    inner = adapters.run_format_tool_call("Inner text.", ToolCall("echo", {"text": "inner"}))
    call = ToolCall("write_note", {"text": f"The earlier reply was:\n{inner}\nEnd of quote."})
    reply = adapters.run_format_tool_call("Saving the quote.", call)
    parsed = parse(reply)
    assert_same_call(parsed, call, reply)
    assert parsed.text == "Saving the quote.", (
        f"expected ParsedResponse.text == 'Saving the quote.', got {parsed.text!r}.\n"
        f"The reply was:\n{reply!r}"
    )


def test_format_does_not_change_the_call_object():
    args = {"text": "unchanged", "nested": {"k": [1, 2]}}
    call = ToolCall("echo", args)
    adapters.run_format_tool_call("Text.", call)
    assert call.name == "echo" and call.args == {"text": "unchanged", "nested": {"k": [1, 2]}}, (
        f"run_format_tool_call must not modify the ToolCall it is given; it is now {call!r}"
    )


# ---------------------------------------------------------- plain text ----

PLAIN_REPLIES = [
    pytest.param("The sum is 42.", id="one-sentence"),
    pytest.param("", id="empty"),
    pytest.param("   \n  ", id="whitespace"),
    pytest.param(
        "Here is what I found:\n\n- The helpdesk is at extension 4410.\n- Payroll closes on the 25th.\n\nAnything else?",
        id="multi-line-with-bullets",
    ),
    pytest.param("I can't do that: the file \"notes.txt\" doesn't exist (error 2).", id="quotes-and-punctuation"),
    pytest.param("Which policy do you mean, the one from March or the one it replaced?", id="question"),
]


@pytest.mark.parametrize("reply", PLAIN_REPLIES)
def test_plain_text_reply_has_no_call_and_no_error(reply):
    """A reply with no tool call is a final answer: tool_call is None, error
    is None, and text is the reply (compared after stripping whitespace)."""
    parsed = parse(reply)
    assert parsed.tool_call is None, (
        f"expected tool_call None for a plain-text reply, got {parsed.tool_call!r}.\n"
        f"The reply was:\n{reply!r}"
    )
    assert parsed.error is None, (
        f"expected error None for a plain-text reply, got {parsed.error!r}.\n"
        f"The reply was:\n{reply!r}"
    )
    assert isinstance(parsed.text, str) and parsed.text.strip() == reply.strip(), (
        f"expected text {reply.strip()!r}, got {parsed.text!r}"
    )


# ----------------------------------------------------------- two calls ----

TWO_CALL_CASES = [
    pytest.param("Adding.", ("add", {"a": 1, "b": 2}), "Looking up.", ("lookup", {"key": "guest_wifi"}), "\n", id="different-calls-with-text"),
    pytest.param("", ("add", {"a": 1, "b": 2}), "", ("lookup", {"key": "guest_wifi"}), "\n", id="different-calls-no-text"),
    pytest.param("", ("echo", {"text": "same"}), "", ("echo", {"text": "same"}), "\n", id="same-call-twice"),
    pytest.param("One.", ("fail", {}), "Two.", ("fail", {}), "\n\n", id="blank-line-between"),
]


@pytest.mark.parametrize("text1,call1,text2,call2,joiner", TWO_CALL_CASES)
def test_two_calls_in_one_reply_is_an_error(text1, call1, text2, call2, joiner):
    """A reply made of two formatted calls, one after the other, sets error
    (a non-empty string) and leaves tool_call None. Neither call is returned."""
    first = adapters.run_format_tool_call(text1, ToolCall(*call1))
    second = adapters.run_format_tool_call(text2, ToolCall(*call2))
    reply = first + joiner + second
    parsed = parse(reply)
    assert parsed.tool_call is None, (
        f"a reply with two calls must not return a call, got {parsed.tool_call!r}.\n"
        f"The reply was:\n{reply!r}"
    )
    assert isinstance(parsed.error, str) and parsed.error.strip(), (
        f"a reply with two calls must set error to a non-empty string, got "
        f"{parsed.error!r}.\nThe reply was:\n{reply!r}"
    )


# ----------------------------------------------------------- truncation ---

TRUNCATION_CALL = ToolCall("write_note", {"text": LONG, "priority": 3})


@pytest.mark.parametrize("text", ["", "Saving it."], ids=["no-text", "with-text"])
def test_truncated_reply_never_returns_a_wrong_call(text):
    """Cut a formatted reply at every position. For every cut,
    run_parse_response must not raise, and must not return a call that
    differs from the one that was formatted: tool_call is either None or has
    exactly the original name and args. (A parser may return the complete
    original call when only the end marker of the format was cut.)"""
    reply = adapters.run_format_tool_call(text, TRUNCATION_CALL)
    for cut in range(1, len(reply)):
        piece = reply[:cut]
        parsed = parse(piece)
        call = parsed.tool_call
        if call is None:
            continue
        assert call.name == TRUNCATION_CALL.name and same_json(call.args, TRUNCATION_CALL.args), (
            f"the reply was cut after {cut} of {len(reply)} characters and parsed to a "
            f"call that was never written.\n"
            f"expected: tool_call None, or {TRUNCATION_CALL.name} with the original args\n"
            f"got:      {call.name} with args {call.args!r}\n"
            f"The cut reply ends with: {piece[-80:]!r}"
        )


@pytest.mark.parametrize("text", ["", "Saving it."], ids=["no-text", "with-text"])
def test_reply_cut_inside_the_arguments_sets_error(text):
    """The formatted call has an argument of several hundred characters, so
    a cut between 25% and 75% of the reply lands inside the arguments, after
    the start of the call. For those cuts error must be set and tool_call must be None: a call
    that was cut off is a malformed reply, not a final answer."""
    reply = adapters.run_format_tool_call(text, TRUNCATION_CALL)
    n = len(reply)
    for cut in sorted({n // 4, n // 3, n // 2, (2 * n) // 3, (3 * n) // 4}):
        piece = reply[:cut]
        parsed = parse(piece)
        assert parsed.tool_call is None, (
            f"the reply was cut after {cut} of {n} characters, inside the arguments; "
            f"expected tool_call None, got {parsed.tool_call!r}"
        )
        assert isinstance(parsed.error, str) and parsed.error.strip(), (
            f"the reply was cut after {cut} of {n} characters, inside the arguments; "
            f"expected error to be a non-empty string, got {parsed.error!r}.\n"
            f"The cut reply ends with: {piece[-80:]!r}"
        )


# ------------------------------------------------------- never raises ----

ODD_REPLIES = [
    "{", "}", "{}", "[]", "<", ">", "</", "```", "```json", "```json\n{", '{"name":', '{"name": "echo"',
    "name: echo", "echo(", "\\", '"', "'", "\x00", "\n\n\n", "null", "None", "<<>>", "{{{{", "}}}}",
    "😀" * 50, "a" * 20000, "{" * 2000, "<a>" * 2000,
]


@pytest.mark.parametrize("reply", ODD_REPLIES, ids=[f"odd-{i}" for i in range(len(ODD_REPLIES))])
def test_parse_never_raises(reply):
    """Whatever the reply is, run_parse_response returns a ParsedResponse,
    and when error is set tool_call is None."""
    parse(reply)


# -------------------------------------------------------- render_tools ----


def fixture_schemas() -> list[dict]:
    return [
        {"name": t.name, "description": t.description, "parameters": t.parameters}
        for t in make_fixture_tools().tools
    ]


def test_render_tools_mentions_every_tool_name():
    rendered = adapters.run_render_tools(fixture_schemas())
    assert isinstance(rendered, str) and rendered.strip(), (
        f"run_render_tools must return a non-empty str, got {rendered!r}"
    )
    missing = [name for name in TOOL_NAMES if name not in rendered]
    assert not missing, f"the rendered tool text does not mention these tool names: {missing}"


def test_render_tools_uses_the_schemas_it_is_given():
    schemas = [
        {
            "name": "zeta_report_9",
            "description": "Build the zeta report.",
            "parameters": {
                "type": "object",
                "properties": {"quarter_label": {"type": "string"}},
                "required": ["quarter_label"],
                "additionalProperties": False,
            },
        }
    ]
    rendered = adapters.run_render_tools(schemas)
    assert "zeta_report_9" in rendered, "the rendered tool text does not mention the tool name zeta_report_9"
    assert "quarter_label" in rendered, (
        "the rendered tool text does not mention the parameter name quarter_label; "
        "the model needs the parameter names to write a valid call"
    )


# ---------------------------------------------------------------- live ----

LIVE_INSTRUCTION = "Carry out the user's request by calling one of the tools described below."


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _arg_matches(got, want) -> bool:
    if _number(want):
        return _number(got) and got == want
    if isinstance(want, str):
        return isinstance(got, str) and got.strip() == want
    return same_json(got, want)


def check_reply(item: dict, reply: str, schemas: dict[str, dict]) -> str | None:
    """None if the reply is a correct call for this request, else the reason."""
    try:
        parsed = adapters.run_parse_response(reply)
    except Exception as exc:
        return f"run_parse_response raised {type(exc).__name__}: {exc}"
    if parsed.error is not None:
        return f"parse error: {parsed.error}"
    if parsed.tool_call is None:
        return "the reply has no tool call"
    call = parsed.tool_call
    if call.name != item["tool"]:
        return f"called {call.name!r}, expected {item['tool']!r}"
    try:
        jsonschema.validate(call.args, schemas[call.name])
    except jsonschema.ValidationError as exc:
        return f"args {call.args!r} do not satisfy the tool's schema: {exc.message}"
    for key, want in item.get("args", {}).items():
        if not _arg_matches(call.args.get(key), want):
            return f"argument {key!r}: expected {want!r}, got {call.args.get(key)!r}"
    for key, parts in item.get("contains", {}).items():
        got = str(call.args.get(key, ""))
        absent = [p for p in parts if p.lower() not in got.lower()]
        if absent:
            return f"argument {key!r}: expected it to contain {absent}, got {got!r}"
    return None


@pytest.mark.live
def test_live_model_writes_correct_calls(live_lm):
    """The model sees one fixed sentence plus your run_render_tools output as
    the system prompt, and one request as the user message. A reply counts as
    correct if run_parse_response returns, without error, a call to the
    expected tool whose args satisfy the tool's schema and match the expected
    values in tests/fixtures/agent_protocol_requests.json. At least
    TOOL_PROTOCOL_MIN_CORRECT of 20 must be correct."""
    schemas = fixture_schemas()
    by_name = {s["name"]: s["parameters"] for s in schemas}
    system = LIVE_INSTRUCTION + "\n\n" + adapters.run_render_tools(schemas)
    items = eval_slice(load_fixture("agent_protocol_requests.json"))

    failures = []
    for item in items:
        reply = live_lm(
            [{"role": "system", "content": system}, {"role": "user", "content": item["request"]}]
        )
        reason = check_reply(item, reply, by_name)
        if reason is not None:
            failures.append(f"{item['id']} ({item['request']!r}): {reason}\n    reply: {reply!r}")

    correct = len(items) - len(failures)
    needed = len(items) * TOOL_PROTOCOL_MIN_CORRECT // 20
    print(f"\ntool_protocol live: {correct} of {len(items)} correct (need {needed}), model {live_lm.model}")
    for line in failures:
        print("  " + line)
    if correct < needed:
        pytest.fail(
            f"{correct} of {len(items)} requests produced a correct call; need at "
            f"least {needed}.\n" + "\n".join(failures),
            pytrace=False,
        )
