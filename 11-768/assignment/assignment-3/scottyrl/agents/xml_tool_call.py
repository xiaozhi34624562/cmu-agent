"""XMLToolCallAgent: the default single-tool-call-per-turn agent (given).

The agent talks to the model through its chat template. It keeps the
episode as a list of chat messages

    system  -> the rules and the tool docs
    user    -> "Task: <goal>" plus the first observation
    assistant / user / assistant / user ...  (one pair per turn)

and asks the policy to render that list to text with the model's own chat
template, so the model sees exactly the format it was trained on (turn
markers, the `<think>` prefill, and so on). Each assistant turn asks for one
XML-style tool call:

    <tool>guess(512)</tool>

Why the prompt is kept in TOKEN space as well
---------------------------------------------
`scottyrl/datagen.py` stitches a whole episode into one training sequence.
That only works if every policy call's prompt is a strict extension of the
previous call's prompt followed by its completion (the "sequence-extension"
property). Re-tokenizing the re-rendered conversation each turn would not
guarantee that: a BPE tokenizer may merge characters across the boundary
between the old text and the new text, producing different tokens for the
same prefix. So the agent keeps `_context_tokens`, the exact token ids the
policy was prompted with, and `_context_text`, the text those tokens stand
for. After each turn it re-renders the full conversation and checks that the
new text starts with `_context_text + completion_text`. When it does, only
the new tail (the closing turn marker, the observation, and the next
generation prompt) is tokenized and appended after the completion tokens,
which the model itself produced. When it does not, the conversation is
re-encoded from scratch and the extension is deliberately broken.

The two template knobs (see `ModelConfig`)
------------------------------------------
`enable_thinking` decides whether the generation prompt ends with `<think>\\n`
(the model writes its reasoning first) or with an empty think block (it
answers directly). The prefill is part of the prompt, so the sampled text
never starts with `<think>`; with thinking on it looks like
"reasoning\\n</think>\\n\\nanswer".

`preserve_thinking_history` decides how earlier assistant turns are
re-rendered. `true` (the default) reproduces the sampled text verbatim, so
the check above succeeds every turn and an episode is one sequence. `false`
strips `<think>...</think>` from earlier turns: the prompt is shorter, the
check fails at every turn boundary, and `stitch_trajectory` emits one
training sequence per turn. That is a real trade-off (context length versus
one long sequence with shared credit), not a bug.

The assistant message stored in `messages` is the completion text minus a
trailing stop sequence (`<|im_end|>`); the template adds the turn marker back
when it renders history. The extension also breaks if the model stops on a
token the template does not write back, e.g. `<|endoftext|>`: the re-rendered
turn ends with `<|im_end|>` instead, so the check above fails and that turn
starts a new training sequence.
"""

from __future__ import annotations

import ast
import re

from scottyrl.agents.base import Agent, AgentAction
from scottyrl.policy import Completion
from scottyrl.types import LLMCall, Observation, Task, ToolCall

TOOL_RE = re.compile(r"<tool>\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*</tool>", re.DOTALL)

SYSTEM_TEMPLATE = """\
You are Scotty, an agent that solves tasks by calling tools.

Rules:
- For tool calling, issue exactly one tool call inside <tool> ... </tool>, written with
  Python-style arguments, e.g. <tool>guess(512)</tool>.
- Output nothing after the tool call.

Tools available in this environment:
{tool_docs}
"""


def system_message(tool_docs: str) -> dict:
    """The system message that opens every episode."""
    return {"role": "system", "content": SYSTEM_TEMPLATE.format(tool_docs=tool_docs)}


def first_user_message(task: Task, first_obs_text: str) -> dict:
    """The first user message: the task goal and the initial observation."""
    return {"role": "user", "content": f"Task: {task.goal}\n{first_obs_text}"}


def strip_trailing_stop(text: str, stop_sequences) -> str:
    """Remove one trailing stop sequence (e.g. `<|im_end|>`) from a completion.

    The chat template re-adds the turn marker when it renders history, so the
    stored assistant content must not carry it.
    """
    for stop in stop_sequences:
        if stop and text.endswith(stop):
            return text[: -len(stop)]
    return text


def parse_tool_call(completion_text: str) -> ToolCall | None:
    """Parse the first `<tool>name(args)</tool>` in a completion.

    Returns None if no well-formed tool call is found. Arguments are parsed
    with `ast.literal_eval`, so only Python literals are allowed (ints,
    strings, dicts, tuples, ...), no arbitrary code execution.
    """
    m = TOOL_RE.search(completion_text)
    if m is None:
        return None
    name, arg_src = m.group(1), m.group(2).strip()
    if not arg_src:
        return ToolCall(name=name, args=(), raw=m.group(0))
    try:
        args = ast.literal_eval(f"({arg_src},)")
    except (ValueError, SyntaxError):
        return None
    return ToolCall(name=name, args=args, raw=m.group(0))


class XMLToolCallAgent(Agent):
    """Chat-template agent that keeps its prompt in token space.

    State per episode:
      messages            the conversation as chat messages
      _context_tokens     the token prompt of the next policy call
      _context_text       the text `_context_tokens` stand for
      _pending_completion the last completion, folded into the context when
                          the next observation arrives
    """

    async def reset(self, task: Task, tool_docs: str) -> None:
        self.task = task
        self.tool_docs = tool_docs
        self.llm_calls = []
        self.messages: list[dict] = []
        self._context_tokens: list[int] = []
        self._context_text: str = ""
        self._pending_completion: Completion | None = None

    def _extend_context(self, obs_text: str) -> None:
        """Fold the pending completion and the new observation into the context."""
        completion = self._pending_completion
        assert completion is not None
        stop_sequences = getattr(self.policy, "stop_sequences", ())
        self.messages.append(
            {"role": "assistant", "content": strip_trailing_stop(completion.text, stop_sequences)}
        )
        self.messages.append({"role": "user", "content": obs_text})
        full_text = self.policy.render(self.messages)

        seen = self._context_text + completion.text
        if full_text.startswith(seen):
            # Extension holds: keep the model's own completion tokens and
            # tokenize only the new tail (turn markers, observation, prefill).
            self._context_tokens = (
                self._context_tokens
                + list(completion.tokens)
                + self.policy.encode(full_text[len(seen) :])
            )
        else:
            # The template rewrote history (thinking stripped): start over.
            # datagen.stitch_trajectory will begin a new sequence here.
            self._context_tokens = self.policy.encode(full_text)
        self._context_text = full_text
        self._pending_completion = None

    async def step(self, obs: Observation) -> AgentAction:
        if not self.messages:
            self.messages = [system_message(self.tool_docs), first_user_message(self.task, obs.text)]
            self._context_text = self.policy.render(self.messages)
            self._context_tokens = self.policy.encode(self._context_text)
        else:
            self._extend_context(obs.text)

        completion = await self.policy.complete(self._context_tokens)
        self.llm_calls.append(
            LLMCall(
                prompt_tokens=list(self._context_tokens),
                completion_tokens=list(completion.tokens),
                completion_logprobs=list(completion.logprobs),
            )
        )
        self._pending_completion = completion
        return AgentAction(tool_call=parse_tool_call(completion.text), text=completion.text)
