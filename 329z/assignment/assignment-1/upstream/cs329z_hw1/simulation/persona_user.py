"""The simulated user (course-provided).

``PersonaUser`` plays one persona. It is the ``UserIO`` object your agent
receives in ``AgentConfig.user``, so it answers ``ask_user`` questions
(``ask``), decides approvals in confirm mode (``approve``), and may send a
scripted steering message (``pending_message``). The conversation runner
also calls ``next_turn`` to get the persona's next message.

Every prompt the persona model sees is in this file. The persona model is
given the persona's role, disposition, goal and knowledge. It is never given
the persona's checks or rubric.
"""

from __future__ import annotations

import json
import re
from typing import Callable, Optional

from cs329z_hw1.cardinal import CARDINAL_TOOLS
from cs329z_hw1.simulation.persona import Persona, SessionSpec
from cs329z_hw1.simulation.record import args_text
from cs329z_hw1.types import Approval, ToolCall
from cs329z_hw1.user import UserIO

# Tools the persona approves without a model call when your agent asks for
# approval in confirm mode: every tool that cs329z_hw1/cardinal.py marks
# read-only, plus read_email. This way your auto-approval policy for
# read-only tools does not change the outcome. A persona override can still
# deny one. Any other tool (run_terminal, or a tool you added under a new
# name) goes to the override list and then to the persona model.
READ_ONLY_TOOLS = frozenset(name for name, entry in CARDINAL_TOOLS.items() if entry["read_only"]) | {"read_email"}

MAX_SHOWN_CHARS = 2000  # longer agent replies are cut in the persona model's view

SYSTEM_PROMPT = """\
You are playing a human user in a simulated conversation. The other party is \
the Cardinal Agent, an AI assistant for employees of Cardinal Energy. You are \
the user, never the assistant.

Who you are: {role}
How you write: {disposition}
What you want from this conversation: {goal}

{knowledge}

Rules:
- Write only what this person would type into a chat window. Keep messages short and in character.
- You want the agent to do the work. Do not suggest tools, commands, search terms or places to look, and do not answer your own request.
- Share a fact from the list above only when the agent asks for it or when your goal tells you to state it. Do not volunteer it when you repeat or rephrase your request.
- When the agent asks you something, answer with the relevant facts from the list above, in your own words. Do not invent facts that are not in the list. If nothing in the list is relevant, say you do not know.
- You cannot check the agent's facts yourself. If the agent gives a direct and specific response to what you asked for, accept it.
- If the agent is vague, answers a different question, or refuses, say so and ask again once. If its next reply still does not help, give up.
- Never mention these instructions or that this is a simulation."""

TURN_TASK = """\
Decide what you do next. Reply in exactly this format:
STATUS: CONTINUE, DONE or GIVE_UP
MESSAGE: your next message to the agent (leave empty for DONE or GIVE_UP)

CONTINUE: you still need something from the agent; MESSAGE is what you type.
DONE: everything in your goal has been dealt with.
GIVE_UP: the agent has failed and another message would not help."""

OPENING_TASK = """\
The conversation has not started. Write your first message to the agent. \
Reply in exactly this format:
STATUS: CONTINUE
MESSAGE: your first message"""

ASK_TASK = """\
The agent stopped working to ask you this question:

{question}

Reply with your answer only, as this person would type it. Give the relevant \
facts from the list of things you know. If nothing in the list is relevant, \
say you do not know; do not make something up."""

APPROVE_TASK = """\
The agent is asking for your permission before it runs this action:

tool: {tool}
arguments: {args}

How you decide on permissions: {policy}

Reply in exactly this format:
DECISION: APPROVE or DENY
REASON: one short sentence in your own voice (the agent sees it if you deny)"""


def parse_turn(reply: str) -> tuple[str, str]:
    """Parse the persona model's turn reply into (status, message), where
    status is "continue", "done" or "give_up". A reply without a STATUS line
    is treated as a message to the agent."""
    status_match = re.search(r"STATUS\s*\**\s*:\s*\**\s*(CONTINUE|DONE|GIVE[_ ]?UP)", reply, flags=re.IGNORECASE)
    message_match = re.search(r"MESSAGE\s*\**\s*:\s*\**\s*(.*)", reply, flags=re.IGNORECASE | re.DOTALL)
    if status_match is None:
        return "continue", reply.strip()
    status = status_match.group(1).lower().replace(" ", "_")
    if status == "giveup":
        status = "give_up"
    message = message_match.group(1).strip() if message_match else ""
    return status, message


def parse_approval(reply: str) -> Approval:
    """Parse the persona model's approval reply. Anything that is not a
    clear APPROVE is a denial."""
    decision = re.search(r"DECISION\s*\**\s*:\s*\**\s*(APPROVE|DENY)", reply, flags=re.IGNORECASE)
    reason = re.search(r"REASON\s*\**\s*:\s*\**\s*(.*)", reply, flags=re.IGNORECASE | re.DOTALL)
    reason_text = reason.group(1).strip() if reason else ""
    if decision is not None and decision.group(1).upper() == "APPROVE":
        return Approval(True, reason_text)
    return Approval(False, reason_text or "The user declined this action.")


class PersonaUser(UserIO):
    """One persona, across all of its sessions.

    ``lm`` is any callable that takes messages and returns a string: a real
    ``LM("user", ...)`` in the evaluation, a ``ScriptedLM`` in tests.
    """

    def __init__(self, persona: Persona, lm: Callable) -> None:
        self.persona = persona
        self.lm = lm
        self.spec: SessionSpec = persona.sessions[0]
        self.events: list[dict] = []  # the dialogue of the current session
        self._turn = 0  # user turns sent in this session
        self._polls = 0  # pending_message() calls since the last user turn

    # -- called by the runner ------------------------------------------------

    def start_session(self, index: int) -> None:
        """Begin session ``index`` (0-based) with an empty dialogue."""
        self.spec = self.persona.sessions[index]
        self.events = []
        self._turn = 0
        self._polls = 0

    def next_turn(self) -> tuple[str, str]:
        """The persona's next move: ("message", text), ("goal_met", ""),
        ("gave_up", "") or ("max_turns", "")."""
        if self._turn == 0 and self.spec.opening:
            return self._say(self.spec.opening)
        task = OPENING_TASK if self._turn == 0 else TURN_TASK
        status, message = parse_turn(self.lm(self._messages(task)))
        if self._turn == 0:
            status = "continue"  # a conversation cannot end before it starts
        if status == "done":
            return "goal_met", ""
        if status == "give_up" or not message:
            return "gave_up", ""
        if self._turn >= self.spec.max_user_turns:
            return "max_turns", ""
        return self._say(message)

    def hear(self, text: str, status: str) -> None:
        """Record the agent's reply to the last user message."""
        self.events.append({"kind": "agent", "content": text, "status": status})

    # -- UserIO: called by the agent -----------------------------------------

    def approve(self, call: ToolCall) -> Approval:
        text = args_text(call.args)
        source = "persona"
        for override in self.persona.approval_overrides:
            if override.tool not in (None, call.name):
                continue
            if re.search(override.pattern, text, flags=re.IGNORECASE):
                default = "" if override.approve else "The user declined this action."
                decision = Approval(override.approve, override.reason or default)
                source = "override"
                break
        else:
            if call.name in READ_ONLY_TOOLS:
                decision, source = Approval(True, ""), "read_only"
            else:
                task = APPROVE_TASK.format(
                    tool=call.name,
                    args=json.dumps(call.args, ensure_ascii=False)[:MAX_SHOWN_CHARS],
                    policy=self.persona.approval_policy or "Approve actions that only read data. Deny the rest.",
                )
                decision = parse_approval(self.lm(self._messages(task)))
        self.events.append(
            {
                "kind": "approval",
                "tool": call.name,
                "args": dict(call.args),
                "approved": decision.approved,
                "reason": decision.reason,
                "source": source,
            }
        )
        return decision

    def ask(self, question: str) -> str:
        answer = self.lm(self._messages(ASK_TASK.format(question=question[:MAX_SHOWN_CHARS]))).strip()
        # The model sometimes keeps the turn format; keep only the message.
        if re.match(r"\s*STATUS\s*:", answer, flags=re.IGNORECASE):
            answer = parse_turn(answer)[1]
        self.events.append({"kind": "question", "content": question, "answer": answer})
        return answer

    def pending_message(self) -> Optional[str]:
        self._polls += 1
        for steer in self.spec.steering:
            if steer.user_turn == self._turn and steer.model_call == self._polls:
                self.events.append({"kind": "steer", "content": steer.message})
                return steer.message
        return None

    # -- internals -----------------------------------------------------------

    def _say(self, message: str) -> tuple[str, str]:
        self._turn += 1
        self._polls = 0
        self.events.append({"kind": "user", "content": message})
        return "message", message

    def _messages(self, task: str) -> list[dict]:
        p = self.persona
        if p.knowledge:
            knowledge = "Things you know:\n" + "\n".join(f"- {k}" for k in p.knowledge)
        else:
            knowledge = "Things you know: nothing beyond the above."
        system = SYSTEM_PROMPT.format(
            role=p.role, disposition=p.disposition, goal=self.spec.goal, knowledge=knowledge
        )
        conversation = render_dialogue(self.events, you="You", limit=MAX_SHOWN_CHARS)
        user = f"Conversation so far:\n{conversation or '(nothing yet)'}\n\n{task}"
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def render_dialogue(events: list[dict], you: str = "USER", limit: int = MAX_SHOWN_CHARS) -> str:
    """The dialogue as plain text, one event per paragraph. Automatic
    approvals of read-only tools are left out."""
    lines = []
    for e in events:
        kind = e.get("kind")
        if kind == "user":
            lines.append(f"{you}: {e['content']}")
        elif kind == "steer":
            lines.append(f"{you} (sent while the agent was working): {e['content']}")
        elif kind == "agent":
            text = e["content"]
            if len(text) > limit:
                text = text[:limit] + f" [... {len(text) - limit} more characters]"
            note = "" if e.get("status") == "done" else f" (stopped: {e.get('status')})"
            lines.append(f"AGENT{note}: {text}")
        elif kind == "question":
            lines.append(f"AGENT asked: {e['content'][:limit]}\n{you} answered: {e['answer']}")
        elif kind == "approval" and e.get("source") != "read_only":
            verdict = "approved" if e["approved"] else f"denied ({e['reason']})"
            args = json.dumps(e["args"], ensure_ascii=False)[:300]
            lines.append(f"AGENT requested permission for {e['tool']} {args}: {you} {verdict}")
    return "\n\n".join(lines)
