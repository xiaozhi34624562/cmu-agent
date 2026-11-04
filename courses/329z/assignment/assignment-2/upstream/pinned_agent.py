"""mini-swe-agent for Harbor with every dependency pinned.

Harbor's built-in ``mini-swe-agent`` runs ``uv tool install mini-swe-agent``
inside the task container without pinning its dependencies, so each run can
pick up a different (and possibly broken) ``litellm``. This subclass installs
the exact versions below instead. Use it with:

    uv run harbor run --agent-import-path pinned_agent:MiniSweAgent ...

You do not need to edit this file.
"""

from __future__ import annotations

import shlex

from harbor.agents.installed.mini_swe_agent import MiniSweAgent as _MiniSweAgent
from harbor.environments.base import BaseEnvironment

MINI_SWE_AGENT_VERSION = "2.4.6"
PYTHON_VERSION = "3.12"
PINS_PATH = "/tmp/mini-swe-agent-pins.txt"

# Generated with `uv pip compile --universal --python-version 3.12` from
# mini-swe-agent==2.4.6 and litellm==1.105.7 (1.106.x crashes on import without
# `mcp`), with filelock overridden to 4.2.6 to clear advisories in filelock 3.x.
PINS = """\
aiohappyeyeballs==2.7.1
aiohttp==3.14.5
aiosignal==1.4.0
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.16.0
attrs==26.1.0
boto3==1.43.123
botocore==1.43.123
certifi==2026.10.23
charset-normalizer==3.5.2
click==8.5.0
colorama==0.4.6 ; sys_platform == 'win32'
datasets==5.1.0
dill==0.4.1
distro==1.9.0
fastuuid==0.14.0
filelock==4.2.6
frozenlist==1.8.0
fsspec==2026.7.0
h11==0.16.0
h2==4.4.1
hf-xet==1.8.0 ; platform_machine == 'AMD64' or platform_machine == 'aarch64' or platform_machine == 'amd64' or platform_machine == 'arm64' or platform_machine == 'x86_64'
hpack==4.2.0
httpcore==1.0.9
httpx==0.28.1
huggingface-hub==1.33.0
hyperframe==6.1.0
idna==3.20
importlib-metadata==8.9.0
jinja2==3.1.6
jiter==0.18.0
jmespath==1.1.0
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
linkify-it-py==2.2.0
litellm==1.105.7
markdown-it-py==4.2.0
markupsafe==3.0.4
mdit-py-plugins==0.6.1
mdurl==0.1.2
mini-swe-agent==2.4.6
multidict==7.2.1
multiprocess==0.70.19
numpy==2.5.4
openai==2.54.0
packaging==26.3
pandas==3.1.0
platformdirs==4.14.3
prompt-toolkit==3.0.53
propcache==0.5.4
pyarrow==26.0.0
pydantic==2.14.2
pydantic-core==2.50.2
pydantic-settings==2.16.2
pygments==2.21.0
python-dateutil==2.9.0.post0
python-dotenv==1.2.4
pyyaml==6.0.3
referencing==0.37.0
regex==2026.9.29
requests==2.34.2
rich==15.0.0
rpds-py==2026.9.1
s3transfer==0.19.3
shellingham==1.5.4
six==1.17.0
sniffio==1.3.1
tenacity==9.2.1
textual==8.2.8
tiktoken==0.14.0
tokenizers==0.23.3
tqdm==4.70.1
typer==0.27.3
typing-extensions==4.16.0
typing-inspection==0.4.4
tzdata==2026.6 ; sys_platform == 'emscripten' or sys_platform == 'win32'
urllib3==2.8.0
wcwidth==0.9.4
xxhash==4.0.2
yarl==1.25.1
zipp==4.1.2
"""


class MiniSweAgent(_MiniSweAgent):
    async def install(self, environment: BaseEnvironment) -> None:
        await self.exec_as_agent(
            environment,
            command=f"printf %s {shlex.quote(PINS)} > {PINS_PATH}",
        )
        # Harbor appends ``=={version}`` to ``uv tool install mini-swe-agent``;
        # temporarily extend it so the install also uses the pinned Python and
        # the full pin list.
        self._version = (
            f"{MINI_SWE_AGENT_VERSION} --python {PYTHON_VERSION} --overrides {PINS_PATH}"
        )
        try:
            await super().install(environment)
        finally:
            self._version = MINI_SWE_AGENT_VERSION
