"""Public tests (given) for the code you build on: tool-call parsing, the two
environments, and how the agent turns an episode into chat messages and
token prompts. These pass out of the box and are not part of your grade;
read them to see what the rollouts you train on look like."""

import asyncio
import json
import re

from scottyrl.agents.xml_tool_call import XMLToolCallAgent, parse_tool_call
from scottyrl.envs.number_search import NumberSearchEnv
from scottyrl.envs.textcraft import RecipeBook, TextCraftEnv
from scottyrl.policy import MockPolicy
from scottyrl.rollout import run_episode
from scottyrl.types import Task, ToolCall


def run(coro):
    return asyncio.run(coro)


# ---------- harness ----------

def test_parse_tool_call():
    tc = parse_tool_call("<think>x</think><tool>guess(512)</tool>")
    assert tc == ToolCall(name="guess", args=(512,), raw="<tool>guess(512)</tool>")

    tc = parse_tool_call('<tool>craft({"m0_i1": 2}, ("m2_i2", 2))</tool>')
    assert tc.name == "craft"
    assert tc.args == ({"m0_i1": 2}, ("m2_i2", 2))

    tc = parse_tool_call('<tool>get_info(["raw_a0", "a1_i5"])</tool>')
    assert tc.args == (["raw_a0", "a1_i5"],)

    assert parse_tool_call("<tool>finish()</tool>").args == ()
    assert parse_tool_call("no tool here") is None
    assert parse_tool_call("<tool>guess(import os)</tool>") is None  # not a literal


# ---------- number search ----------

def make_ns_task(low=0, high=100, target=42, max_steps=9):
    return Task(goal="find", id="ns", max_steps=max_steps,
                info={"low": low, "high": high, "target": target})


def test_number_search_feedback():
    async def flow():
        env = NumberSearchEnv(make_ns_task())
        await env.reset()
        assert "too low" in (await env.step(ToolCall("guess", (10,)))).text
        assert "too high" in (await env.step(ToolCall("guess", (90,)))).text
        obs = await env.step(ToolCall("guess", (42,)))
        assert obs.done and obs.reward == 1.0
    run(flow())


def test_number_search_budget_and_invalid():
    async def flow():
        env = NumberSearchEnv(make_ns_task(max_steps=2))
        await env.reset()
        obs = await env.step(None)  # unparseable action costs a step
        assert "Could not parse" in obs.text and not obs.done
        obs = await env.step(ToolCall("guess", (1,)))
        assert obs.done and obs.reward == 0.0
    run(flow())


# ---------- the agent's chat messages and token prompts ----------
#
# MockPolicy renders messages as "<role>\ncontent\n" and tokenizes text as
# its UTF-8 bytes, so these checks need no tokenizer. The real chat template
# (scottyrl/chat_templates/qwen3_5.jinja) has the same two properties the
# tests below rely on: it re-renders earlier assistant turns verbatim, and it
# adds the turn marker itself, so the stop token is not stored in history.

STOP = "<|im_end|>"


class StopTokenPolicy(MockPolicy):
    """MockPolicy whose completions end with a stop token, like a real
    sampler's, and whose template writes that token back for every earlier
    assistant turn, like a real chat template."""

    stop_sequences = [STOP]

    def render(self, messages, add_generation_prompt=True):
        text = "".join(
            f"<{m['role']}>\n{m['content']}" + (f"{STOP}\n" if m["role"] == "assistant" else "\n")
            for m in messages
        )
        return text + ("<assistant>\n" if add_generation_prompt else "")


def test_episode_messages_hold_the_task_and_stop_stripped_completions():
    script = [f"<tool>guess(3)</tool>{STOP}", f"<tool>guess(7)</tool>{STOP}"]
    policy = StopTokenPolicy(script)
    agent = XMLToolCallAgent(policy)
    traj = run(run_episode(agent, NumberSearchEnv(make_ns_task(target=7, max_steps=4))))
    assert traj.reward == 1.0 and len(traj.calls) == 2

    roles = [m["role"] for m in agent.messages]
    assert roles == ["system", "user", "assistant", "user"]
    assert "Tools available" in agent.messages[0]["content"]
    assert agent.messages[1]["content"].startswith("Task: find\n")
    # The stored assistant turn is the completion minus its stop token; the
    # last completion is never appended (no observation follows it).
    assert agent.messages[2]["content"] == "<tool>guess(3)</tool>"
    # The stop token stays in the completion tokens the model produced ...
    assert bytes(traj.calls[0].completion_tokens).decode() == script[0]
    # ... and the extension still holds, because the template writes it back.
    c0, c1 = traj.calls
    seen = c0.prompt_tokens + c0.completion_tokens
    assert c1.prompt_tokens[: len(seen)] == seen


def test_prompts_extend_in_token_space_across_turns():
    task = make_ns_task(target=7, max_steps=4)
    policy = MockPolicy(["<tool>guess(3)</tool>", "<tool>guess(7)</tool>"])
    agent = XMLToolCallAgent(policy)
    traj = run(run_episode(agent, NumberSearchEnv(task)))
    assert traj.reward == 1.0 and traj.num_steps == 2 and len(traj.calls) == 2

    # prompt_1 == prompt_0 + completion_0 + (observation + generation prompt):
    # this is what lets datagen stitch an episode into one training sequence.
    c0, c1 = traj.calls
    seen = c0.prompt_tokens + c0.completion_tokens
    assert c1.prompt_tokens[: len(seen)] == seen
    tail = bytes(c1.prompt_tokens[len(seen):]).decode()
    assert tail.startswith("\n<user>\n") and "too low" in tail and tail.endswith("<assistant>\n")
    # Each token prompt is exactly the rendered conversation at that point.
    assert c0.prompt_tokens == policy.encode(policy.render(agent.messages[:2]))
    assert c1.prompt_tokens == policy.encode(policy.render(agent.messages))


THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


class ThinkStrippingPolicy(MockPolicy):
    """MockPolicy whose template drops <think> blocks from earlier assistant
    turns, which is what `preserve_thinking_history: false` does."""

    def render(self, messages, add_generation_prompt=True):
        stripped = [
            {**m, "content": THINK_RE.sub("", m["content"])} if m["role"] == "assistant" else m
            for m in messages
        ]
        return super().render(stripped, add_generation_prompt)


def test_history_rewrite_forces_a_reencode_and_breaks_the_extension():
    script = [
        "<think>\nstart low\n</think>\n\n<tool>guess(2)</tool>",
        "<think>\nhigher\n</think>\n\n<tool>guess(9)</tool>",
        "<think>\nbisect\n</think>\n\n<tool>guess(7)</tool>",
    ]
    policy = ThinkStrippingPolicy(script)
    agent = XMLToolCallAgent(policy)
    traj = run(run_episode(agent, NumberSearchEnv(make_ns_task(target=7, max_steps=4))))
    assert traj.reward == 1.0 and len(traj.calls) == 3

    calls = traj.calls
    for i, (prev, nxt) in enumerate(zip(calls, calls[1:])):
        # The next prompt still starts with the previous prompt ...
        assert nxt.prompt_tokens[: len(prev.prompt_tokens)] == prev.prompt_tokens
        # ... but not with prompt + completion: the sampled think block is gone,
        # so datagen.stitch_trajectory must start a new sequence here.
        seen = prev.prompt_tokens + prev.completion_tokens
        assert nxt.prompt_tokens[: len(seen)] != seen
        # The agent re-encoded the rewritten conversation from scratch.
        assert nxt.prompt_tokens == policy.encode(policy.render(agent.messages[: 2 + 2 * (i + 1)]))
        assert b"<think>" not in bytes(nxt.prompt_tokens)
    # The stored messages still hold the verbatim completions.
    assert [m["content"] for m in agent.messages if m["role"] == "assistant"] == script[:2]


# ---------- textcraft ----------

TINY_BOOK = RecipeBook.from_dict({
    "base_items": ["raw_x", "raw_y"],
    "recipes": {
        "gear": [{"ingredients": {"raw_x": 2, "raw_y": 1}, "result_count": 2}],
        "orb": [{"ingredients": {"gear": 1}, "result_count": 1}],
    },
})


def make_tc_task(targets=None, inventory=None, max_steps=10):
    return Task(
        goal="Craft the following items: 1x orb", id="tc", max_steps=max_steps,
        info={
            "target_items": targets or {"orb": 1},
            "initial_inventory": inventory or {"raw_x": 4, "raw_y": 2},
        },
    )


def test_textcraft_happy_path():
    async def flow():
        env = TextCraftEnv(make_tc_task(), recipe_book=TINY_BOOK)
        obs = await env.reset()
        assert "Target: craft 1x orb" in obs.text

        obs = await env.step(ToolCall("craft", ({"raw_x": 2, "raw_y": 1}, ("gear", 2))))
        assert "Successfully crafted 2 gear(s)" in obs.text
        obs = await env.step(ToolCall("craft", ({"gear": 1}, ("orb", 1))))
        assert "Successfully crafted 1 orb(s)" in obs.text
        obs = await env.step(ToolCall("finish", ("done",)))
        assert obs.done and obs.reward == 1.0
    run(flow())


def test_textcraft_strict_craft_rules():
    async def flow():
        env = TextCraftEnv(make_tc_task(), recipe_book=TINY_BOOK)
        await env.reset()
        # wrong ingredient amount (recipe needs exactly 2 raw_x per craft)
        obs = await env.step(ToolCall("craft", ({"raw_x": 3, "raw_y": 1}, ("gear", 2))))
        assert "Wrong amount" in obs.text
        # target count not divisible by result_count (2)
        obs = await env.step(ToolCall("craft", ({"raw_x": 2, "raw_y": 1}, ("gear", 3))))
        assert "not divisible" in obs.text
        # extra ingredients rejected
        obs = await env.step(ToolCall("craft", ({"raw_x": 2, "raw_y": 1, "gear": 1}, ("gear", 2))))
        assert "Extra ingredients" in obs.text
        # no recipe
        obs = await env.step(ToolCall("craft", ({"raw_x": 1}, ("nonexistent", 1))))
        assert "No recipe found" in obs.text
    run(flow())


def test_textcraft_finish_requires_crafted_delta():
    async def flow():
        # target item already in initial inventory -> does not count
        task = make_tc_task(targets={"gear": 1}, inventory={"gear": 1, "raw_x": 1})
        env = TextCraftEnv(task, recipe_book=TINY_BOOK)
        await env.reset()
        obs = await env.step(ToolCall("finish", ()))
        assert obs.done and obs.reward == 0.0
    run(flow())


def test_textcraft_get_info_and_inventory():
    async def flow():
        env = TextCraftEnv(make_tc_task(), recipe_book=TINY_BOOK)
        await env.reset()
        obs = await env.step(ToolCall("get_info", (["orb", "raw_x", "unknown"],)))
        infos = {i["item"]: i for i in json.loads(obs.text)}
        assert infos["orb"]["can_craft"] and infos["orb"]["crafting_depth"] == 2
        assert infos["raw_x"]["is_base"] and infos["raw_x"]["in_inventory"] == 4
        assert not infos["unknown"]["can_craft"]
        obs = await env.step(ToolCall("view_inventory", ()))
        assert json.loads(obs.text) == {"raw_x": 4, "raw_y": 2}
    run(flow())
