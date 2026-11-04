"""Official HumanEval/0 checks, adapted to run against the Harbor task state."""

import sys

sys.path.insert(0, "/app")

from humaneval_0 import has_close_elements


def check(candidate):
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) is True
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) is False
    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) is True
    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) is False
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) is True
    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) is True
    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) is False


check(has_close_elements)
