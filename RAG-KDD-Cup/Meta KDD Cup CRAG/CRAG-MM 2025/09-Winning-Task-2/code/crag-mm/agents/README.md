# 🤖 CRAG-MM Agent Development Guide

Welcome to the CRAG-MM agent development playground! This directory is where participants can implement their vision-language models for the CRAG-MM benchmark.

We recommend that you put everything you need for the agent to run in this repo for a smoother submission/evaluation process. However, you're free to organize your code as you prefer.

## 🎯 Structure of This Directory

```
agents/
├── base_agent.py                # Base class that all agents must inherit from
├── random_agent.py              # Sample random response agent (reference implementation)
├── vanilla_llama_vision_agent.py # Sample vision-language model agent using Llama-Vision
├── rag_agent.py                 # Sample RAG-based agent with search capabilities
└── user_config.py               # Configuration file to specify which agent to use
```

## 🧪 Sample Agents

We've provided three sample agents to help you get started:

1. **RandomAgent** 🎲
   - A simple agent that generates random responses
   - Perfect for testing the evaluation pipeline
   - Located in `random_agent.py`

2. **LlamaVisionModel** 🦙
   - A vision-language model based on Meta's Llama 3.2 11B Vision Instruct model
   - Handles both single-turn and multi-turn conversations
   - Located in `vanilla_llama_vision_agent.py`

3. **SimpleRAGAgent** 🔍
   - A RAG (Retrieval-Augmented Generation) based agent
   - Uses unified search pipeline for retrieving relevant information
   - Demonstrates how to combine vision and text search
   - Located in `rag_agent.py`

## 🛠️ Creating Your Own Agent

To create your own agent, follow these steps:

1. Create a new Python file in the `agents` directory
2. Import and inherit from `BaseAgent`:
   ```python
   from typing import Dict, List, Any
   from PIL import Image
   from agents.base_agent import BaseAgent
   from cragmm_search.search import UnifiedSearchPipeline

   class YourAgent(BaseAgent):
       def __init__(self, search_pipeline: UnifiedSearchPipeline):
           # Initialize your model here
           # You have 10 minutes for initialization
           super().__init__(search_pipeline)
           # Note: The web-search will be disabled in case of Task 1 (Single-source Augmentation) - so only image-search can be used in that case.

       def get_batch_size(self) -> int:
           # Return your preferred batch size (1-16)
           return 8

       def batch_generate_response(
           self,
           queries: List[str],
           images: List[Image.Image],
           message_histories: List[List[Dict[str, Any]]],
       ) -> List[str]:
           # Implement your batch response generation logic here
           # Process all queries in the batch and return a list of responses
           # This function should respond in at most: 10s * self.get_batch_size() 
           responses = []
           for query, image, message_history in zip(queries, images, message_histories):
               # Your processing logic here
               responses.append("Your response for this query")
           return responses
   ```

### ⚡ Performance Constraints

- **Initialization Time**: 10 minutes maximum
- **Batch Processing**: The evaluator will process multiple queries at once based on your `get_batch_size()`
- **Batch Response Time**: `10 s * agent.get_batch_size()` for each `agent.batch_generate_response(..)` call.
- **Memory Usage**: Be mindful of GPU memory usage. Your submissions will have access to a single NVIDIA L40s GPU with 48GB of GPU Memory.

### 📝 Method Signatures

Your agent must implement the following methods:

```python
def get_batch_size(self) -> int:
    # Return a value between 1-16
```

```python
def batch_generate_response(
    self,
    queries: List[str],
    images: List[Image.Image],
    message_histories: List[List[Dict[str, Any]]],
) -> List[str]:
```

Parameters:
- `queries`: List of questions from users
- `images`: List of PIL Image objects (one per query)
- `message_histories`: List of conversation histories (one per query)

The message_histories format is:
- For single-turn conversations: Empty list `[]`
- For multi-turn conversations: List of previous turns in the format:
  ```
  [
    {"role": "user", "content": "first user message"},
    {"role": "assistant", "content": "first assistant response"},
    {"role": "user", "content": "follow-up question"},
    {"role": "assistant", "content": "follow-up response"},
    ...
  ]
  ```

## 🔧 Configuration

To use your agent:

1. Edit `user_config.py`
2. Import your agent class
3. Assign it to `UserAgent`:
   ```python
   from your_agent_file import YourAgent
   UserAgent = YourAgent
   ```

## 📦 Using models on HuggingFace 🤗

During evaluation, internet access will be disabled and `HF_HUB_OFFLINE=1` environment variable will be set. If you want to use a model available HuggingFace, please include a reference to its model spec in `aicrowd.json` as: 
```
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
            "ignore_patterns": "*.md",            
        },
        ...
    ]
}
```

The evaluators will ensure that before the evaluation begins (in a container without network access), these models are available in the local huggingface cache of the evaluation container.

The keys for the `model_spec` dictionary can include any parameter supported by the [`huggingface_hub.snapshot_download`](https://huggingface.co/docs/huggingface_hub/v0.30.2/en/package_reference/file_download#huggingface_hub.snapshot_download) function.

**Important:**
- Models specified must be publicly available, or the [aicrowd Hugging Face account](https://huggingface.co/aicrowd) must be explicitly granted access.
- If your model repository is private, you must grant access to the [`aicrowd` user](https://huggingface.co/aicrowd). Otherwise, your submission will fail.

**Granting access to private repositories:**
To provide access to a private repository, create an organization on Hugging Face specifically for your participation in this competition. Create your private repository within this organization and add the `aicrowd` user as a member to ensure seamless access.


### ⚠️ Important Notes

1. **Model Access**: Ensure that the `aicrowd` HuggingFace account has access to all models specified in `hf_models`
2. **Offline Mode**: Any model not specified in `aicrowd.json` will fail during evaluation
3. **Model Download**: We will download all specified models before evaluation starts
4. **Access Control**: If your model is private, make sure to:
   - Grant access to the `aicrowd` HF account
   - Include the model in `hf_models`
   - Use the correct model ID (org/model-name)

## 🧪 Local Evaluation

We provide a `local_evaluation.py` script to evaluate your agent:

```bash
python local_evaluation.py \
    --dataset-type single-turn \
    --split validation \
    --num-conversations 100 \
    --display-conversations 3 \
    --eval-model gpt-4o-mini \
    --suppress-web-search-api # Only include when evaluatingn for Single Source Augmentation Track, where web-search-api is not available but image-search-api is available
```

Options:
- `--dataset-type`: Choose between "single-turn" or "multi-turn"
- `--split`: Dataset split to use ("validation", "public_test")
- `--num-conversations`: Number of conversations to evaluate (-1 for all)
- `--suppress-web-search-api`: Disable the search API for testing Single-source Augmentation
- `--display-conversations`: Number of example conversations to display
- `--eval-model`: OpenAI model for semantic evaluation (use 'None' to disable)
- `--output-dir`: Directory to save evaluation results
- `--no_progress`: Disable progress bar
- `--revision`: Dataset revision/version to use
- `--num-workers`: Number of parallel evaluation workers

## 🎯 Evaluation Metrics

The evaluation script calculates:
- Exact match accuracy
- Semantic accuracy (using LLM-as-judge)
- Missing rate ("I don't know" responses)
- Hallucination rate
- Truthfulness score
- Multi-turn conversation score (for multi-turn evaluations)

## 🔍 Working with the Search Pipeline

For RAG-based agents, you can use the provided `UnifiedSearchPipeline`:

```python
# Using the search pipeline
search_results = self.search_pipeline(query, k=3)

# Each result contains:
for result in search_results:
    snippet = result.get('page_snippet', '')
    # Use the snippet in your prompt
```

## 🚀 Getting Started

1. Clone the repository
2. Install dependencies
3. Implement your agent by inheriting from `BaseAgent`
4. Update `user_config.py` to use your agent
5. Run local evaluation
6. Iterate and improve!

Happy coding! 🚀
