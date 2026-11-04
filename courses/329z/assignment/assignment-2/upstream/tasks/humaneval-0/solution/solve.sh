#!/bin/bash
set -euo pipefail

python - <<'PY'
from pathlib import Path

path = Path("/app/humaneval_0.py")
text = path.read_text()
text = text.replace(
    "    pass\n",
    """    for index, element in enumerate(numbers):
        for other_index, other_element in enumerate(numbers):
            if index != other_index and abs(element - other_element) < threshold:
                return True
    return False
""",
)
path.write_text(text)
PY
