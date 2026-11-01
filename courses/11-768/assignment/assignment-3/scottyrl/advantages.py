"""Advantage estimation. *** STUDENT IMPLEMENTATION FILE ***

Implement `compute_group_advantages` exactly to this contract; the grading
suite calls it directly.
"""

from __future__ import annotations

from typing import Sequence


def compute_group_advantages(
    rewards: Sequence[float],
    method: str = "grpo",
) -> list[float] | None:
    """Compute per-trajectory advantages for a group of rollouts of one task.

    Contract:
      - method="reinforce": each trajectory's advantage is its raw episode
        reward, no baseline. (Used with group size 1.)
      - method="grpo": group-relative advantages, each trajectory's reward
        minus the mean reward of its group. Requires a group of at least 2
        (raise ValueError otherwise). If every reward in the group is
        identical, the group is *degenerate*: the centered advantages would
        be zero everywhere, so there is no learning signal; return None so
        the caller can skip the whole group. Note, we do not divide by the 
        std dev of the group rewards (similar to DR. GRPO)
      - Any other method: raise ValueError.

    Returns: a plain Python list of floats aligned with `rewards` (same
    length and order), or None for a degenerate GRPO group. "Identical"
    means exactly equal rewards (no tolerance).

    A note on naming: this is the group-mean baseline WITHOUT the per-group
    std-dev normalization of the original GRPO paper (i.e. the Dr.GRPO
    variant, which drops the std term to avoid biasing updates by group
    difficulty). See the handout's background section.
    """
    # TODO(student): implement this function.
    raise NotImplementedError
