# Submission Guidelines 🚀

Ready to showcase your **CRAG-MM** solution on the leaderboard? Follow the steps below to **submit** your model to the **Meta CRAG-MM** challenge with confidence! 🎉

---

## 1. Repository & Setup

### 1.1 Clone the Starter Kit 🏁

1. **Fork** the official **[Meta CRAG-MM Starter Kit](https://gitlab.aicrowd.com/aicrowd/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2025/meta-comprehensive-rag-benchmark-starter-kit/-/tree/main)** repository from the challenge page.
2. **Clone** your fork locally:
   ```bash
   git clone git@gitlab.aicrowd.com:<YOUR-AICROWD-USERNAME>/<YOUR-FORK>.git
   cd <YOUR-FORK>
   ```

### 1.2 Add Your Agent Code 🧩

1. Navigate to the `agents/` directory in your cloned repo.
2. Create or modify a file (e.g., `my_agent.py`) that implements the [BaseAgent](../agents/base_agent.py) interface.
3. In `agents/user_config.py`, **import** your new agent class and **assign** it to `UserAgent`.

> **Remember**: During evaluation, your code will run in an **offline environment** (no internet!). This means you must **pre-download** or reference **Hugging Face** models in such a way that they are available offline. See [below](#link-to-hf) for instructions on specifying HF models.

---

## 2. Specifying Models & Dependencies

### 2.1 aicrowd.json 🗒️

In your repository’s root directory, create or update the `aicrowd.json` file to specify key details for your submission:

```json
{
    "challenge_id": "single-source-augmentation",
    "gpu": true,
    "hf_models": [
        {
            "repo_id": "meta-llama/Llama-3.2-11B-Vision-Instruct",
            "revision": "main"
        },
        {
            "repo_id": "your-org/your-model",
            "revision": "your-custom-revision",
            "ignore_patterns": "*.md"
        }
    ]
}
```

- **`challenge_id`**: Select from one of the following:
  - `"single-source-augmentation"`
  - `"multi-source-augmentation"`
  - `"multi-turn-qa"`

- **`gpu`**: Set to `true` if GPU acceleration is required, else `false`.

- **`hf_models`**: List all Hugging Face models your agent uses. These models **must** be publicly accessible or explicitly shared with the `aicrowd` Hugging Face account. Before evaluation, these models will be pre-downloaded and cached locally in a container with no internet access (`HF_HUB_OFFLINE=1`).

  > The `hf_models` entries support parameters compatible with [`huggingface_hub.snapshot_download`](https://huggingface.co/docs/huggingface_hub/v0.30.2/en/package_reference/file_download#huggingface_hub.snapshot_download).

For detailed instructions on securely setting up your submissions as Public Gated Hugging Face models, please refer to [Using Gated Hugging Face Models in Your Submission 🔒](huggingface-gated-models.md).

### 2.3 requirements.txt 🗒️

All Python dependencies must be declared in `requirements.txt`. For example:

```
torch>=2.0.0
transformers>=4.36.0
pillow>=10.0.0
numpy>=1.24.0
# Include any additional libraries your agent needs
```

### 2.4 Dockerfile 🐳 (Optional)

If you wish to further customize your environment, you can edit or create a `Dockerfile` in your repository root. For example:

```dockerfile
FROM nvidia/cuda:12.2.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y git wget && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# (Optional) Copy your code
COPY . /app

# (Optional) Specify environment variables
ENV HF_HUB_OFFLINE=1
```

---

## 3. Workflow for Submissions

### 3.1 Commit & Push Your Code 🌐

Once you have:
1. Implemented or updated your agent in `agents/`
2. Specified your models in `aicrowd.json`
3. Listed dependencies in `requirements.txt`
4. (Optional) Updated the `Dockerfile`

Commit and push your changes:
```bash
git add .
git commit -m "Add my custom agent"
git push origin main
```

### 3.2 Tagging a Submission ✨

**Create a Git tag** that starts with `submission-<version>` to trigger a submission:

```bash
git tag submission-v1.0
git push origin submission-v1.0
```
This **tagged commit** is used to build and evaluate your model, generating a score on the leaderboard. You can create as many `submission-*` tags as you like (e.g., `submission-v1.1`, `submission-v2.0`, etc.).

---

## 4. Hardware & Evaluation Environment

1. **Hardware**: Your code will run on an **NVIDIA L40s GPU** with 4 vCPUs, **32GB RAM**, and **48GB of GPU Memory** and no internet access (`HF_HUB_OFFLINE=1`).
2. **Initialization Time**: You have **10 minutes** to download models and set up your environment.
3. **Response Time**: Each call to your agent’s `batch_generate_response()` must finish within **10 seconds x agent.get_batch_size()** .
4. **No Internet**: Any code that tries to reach out to external URLs will fail. Ensure your model and all dependencies are accessible offline via `hf_models` or your Docker image.

---

## 5. Tips & Examples

### 5.1 Example aicrowd.json
```json
{
    "challenge_id": "multi-source-augmentation",
    "gpu": true,
    "hf_models": [
        {
            "repo_id": "meta-llama/Llama-3.2-11B-Vision-Instruct",
            "revision": "main"
        },
        {
            "repo_id": "your-org/your-model",
            "revision": "your-custom-revision",
            "ignore_patterns": "*.md",            
        },
        ...
    ]
}
```
- Submits to the **multi-source-augmentation** track
- Requests GPU resources
- Two HF models: the Llama 3.2 11B vision instruct model + your custom vision model

### 5.2 Example requirements.txt
```
torch>=2.0.0
transformers>=4.36.0
pillow>=10.0.0
numpy>=1.24.0
some-retrieval-lib>=0.1.3
```

### 5.3 Example Dockerfile
```dockerfile
FROM python:3.10-slim-bookworm

RUN pip install --progress-bar off --no-cache-dir -U pip==21.0.1
COPY requirements.txt /tmp/requirements.txt
RUN pip install --progress-bar off --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/aicrowd
COPY . .

```

---

## 6. Choosing a Track

In `aicrowd.json`, set `"challenge_id"` to one of:

1. **`"single-source-augmentation"`**
2. **`"multi-source-augmentation"`**
3. **`"multi-turn-qa"`**

Whichever ID you choose determines **which task** your submission competes in. 🏆

---

## 7. Next Steps

- Write or refine your agent code in `agents/`
- Update `aicrowd.json` with the correct `challenge_id` and `hf_models`
- Tag your submission with `submission-<version>` and push it.
```
git commit -am 'Your message'
git tag -am 'submission-<A_GREAT_NAME>' submission-<A_GREAT_NAME>
git push origin submission-<A_GREAT_NAME>
```
- 🎉 Watch your scoreboard results on the challenge page!

## 8. Troubleshooting & Best Practices

1. **Model Access**: Confirm that the **`aicrowd`** Hugging Face account has permission to pull your private models.
2. **Local Testing**: Use `python local_evaluation.py` to confirm basic correctness before tagging a submission.
3. **Performance Optimization**: For large models, consider quantization or other speed-ups to meet runtime constraints.
4. **Multiple Submissions**: Tag different versions (e.g. `submission-v1.0`, `submission-v1.1`) for multiple attempts.

> **Pro Tip**: Keep an eye on your Docker build logs to ensure it doesn't exceed time or memory limits.

---


**We can’t wait to see your creative solutions!** 🤖🌟 Happy hacking!
