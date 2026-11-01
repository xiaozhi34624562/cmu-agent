"""Course-provided user interface for the interactive layer.

Your agent never reads the keyboard. When it needs the human, it calls one of
the three methods of the ``UserIO`` object in ``AgentConfig.user``. The tests
pass a ``ScriptedUser``; the evaluation passes an LLM-simulated persona; and
``ConsoleUser`` lets you talk to your agent yourself.
"""

from __future__ import annotations

from typing import Optional, Sequence

from cs329z_hw1.types import Approval, ToolCall


class UserIO:
    """The three ways your agent reaches the human."""

    def approve(self, call: ToolCall) -> Approval:
        """Ask the user whether ``call`` may run. Used in confirm mode."""
        raise NotImplementedError

    def ask(self, question: str) -> str:
        """Put the model's ask_user question to the user and return the answer."""
        raise NotImplementedError

    def pending_message(self) -> Optional[str]:
        """A steering message the user sent while the agent was working, or
        None. Call this before every model call; a returned message is
        consumed (the next call returns None unless another arrived)."""
        return None


class ScriptedUser(UserIO):
    """A user that follows a script. Used by the deterministic tests.

    approvals: one entry per approve() call, each True, False, or an Approval.
    answers:   one entry per ask() call.
    steering:  {n: message} delivers ``message`` on the n-th pending_message()
               call (0-based).
    Every interaction is recorded in ``.log``.
    """

    def __init__(
        self,
        approvals: Sequence[bool | Approval] = (),
        answers: Sequence[str] = (),
        steering: Optional[dict[int, str]] = None,
    ) -> None:
        self._approvals = list(approvals)
        self._answers = list(answers)
        self._steering = dict(steering or {})
        self._polls = 0
        self.log: list[tuple] = []

    def approve(self, call: ToolCall) -> Approval:
        if not self._approvals:
            raise AssertionError(
                f"approve() was called for {call.name}({call.args}) but the script "
                "has no approvals left"
            )
        decision = self._approvals.pop(0)
        if not isinstance(decision, Approval):
            decision = Approval(bool(decision), "" if decision else "The user declined this action.")
        self.log.append(("approve", call.name, dict(call.args), decision.approved))
        return decision

    def ask(self, question: str) -> str:
        if not self._answers:
            raise AssertionError(f"ask() was called with {question!r} but the script has no answers left")
        answer = self._answers.pop(0)
        self.log.append(("ask", question, answer))
        return answer

    def pending_message(self) -> Optional[str]:
        message = self._steering.pop(self._polls, None)
        self._polls += 1
        if message is not None:
            self.log.append(("steer", message))
        return message


class ConsoleUser(UserIO):
    """A real person at the terminal."""

    def approve(self, call: ToolCall) -> Approval:
        print(f"\nThe agent wants to run {call.name} with {call.args}")
        reply = input("Allow? [y/N, or type a reason to deny] ").strip()
        if reply.lower() in ("y", "yes"):
            return Approval(True)
        return Approval(False, reply if reply.lower() not in ("", "n", "no") else "The user declined this action.")

    def ask(self, question: str) -> str:
        print(f"\nThe agent asks: {question}")
        return input("> ").strip()
