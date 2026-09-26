# Baseline Implementations 🚀

This document highlights the **baseline agents** available in the **`agents`** directory of this repository. These agents showcase different approaches to solving the **Meta CRAG-MM** benchmark. We hope you'll find them a **fun** and **instructive** starting point for your own creations! 🤖

---

## 🎯 Why Baselines?

Baselines demonstrate how to implement agents that comply with the [submission guidelines](../docs/submission.md) and the [agent interface](../agents/README.md). They also provide reference points for **local evaluation** using `local_evaluation.py`. You can experiment with them, adapt their logic, or build entirely new solutions!

---

## 1. **RandomAgent** 🎲

**File**: [`agents/random_agent.py`](../agents/random_agent.py)  
**Class Name**: `RandomAgent`

### Key Features

- **Random String Generator**: Produces random strings of letters of variable length (between 2 and 16 characters).  
- **Reference Implementation**: Illustrates the agent interface with minimal overhead.
- **Batch Processing**: Demonstrates how to handle batch queries efficiently.
- **No Real Intelligence**: Strictly for testing the evaluation pipeline.

### Usage Example

```python
from agents.random_agent import RandomAgent
from cragmm_search.search import UnifiedSearchPipeline

# Initialize the agent
search_pipeline = UnifiedSearchPipeline(...)  # Or None for Single-source Augmentation track
agent = RandomAgent(search_pipeline)

# Get batch size for evaluation
batch_size = agent.get_batch_size()  # Returns 16

# Process a batch of queries
queries = ["What is this?", "Describe this image."]
images = [image1, image2]  # PIL Image objects
message_histories = [[], []]  # Empty for single-turn conversations
responses = agent.batch_generate_response(queries, images, message_histories)
print(responses)  # Outputs random strings, e.g. ["abDUq hf", "xYz pQr"]
```

---

## 2. **LlamaVisionModel** 🦙

**File**: [`agents/vanilla_llama_vision_agent.py`](../agents/vanilla_llama_vision_agent.py)  
**Class Name**: `LlamaVisionModel`

### Key Features

- **Vision-Language Model**: Uses `meta-llama/Llama-3.2-11B-Vision-Instruct` with vLLM for efficient inference.
- **Image + Text Processing**: Handles PIL Image objects and text queries together.
- **Conversation History**: Supports multi-turn conversations with conversation history.
- **Batch Processing**: Efficiently processes multiple queries and images in parallel.
- **Optimized Configuration**: Includes settings for running on a single NVIDIA L40s GPU.

### Usage Example

```python
from PIL import Image
from agents.vanilla_llama_vision_agent import LlamaVisionModel
from cragmm_search.search import UnifiedSearchPipeline

# Initialize the agent
search_pipeline = UnifiedSearchPipeline(...)  # Or None for Single-source Augmentation track
agent = LlamaVisionModel(search_pipeline)

# Process a batch of queries
queries = ["Where was this photo taken?", "What can you see in this image?"]
images = [Image.open("path/to/image1.jpg"), Image.open("path/to/image2.jpg")]
message_histories = [[], []]  # Empty for single-turn conversations

responses = agent.batch_generate_response(queries, images, message_histories)
print(responses)
```

> **Note**: This agent demonstrates how to efficiently use the Llama Vision model with the vLLM library for faster inference.

---

## 3. **SimpleRAGAgent** 🔎

**File**: [`agents/rag_agent.py`](../agents/rag_agent.py)  
**Class Name**: `SimpleRAGAgent`

### Key Features

- **Retrieval-Augmented Generation**: Uses `UnifiedSearchPipeline` to gather external text snippets based on image content and queries.
- **Batch Processing**: Efficiently processes multiple queries in a single batch.
- **Two-Step Approach**:
  1. First summarizes images to generate effective search terms
  2. Then retrieves relevant information and incorporates it into the responses
- **Enhanced Prompting**: Structures prompts with retrieved context for better responses.

### Usage Example

```python
from PIL import Image
from agents.rag_agent import SimpleRAGAgent
from cragmm_search.search import UnifiedSearchPipeline

# Initialize the agent (RAG agent requires a search pipeline)
search_pipeline = UnifiedSearchPipeline(...)
agent = SimpleRAGAgent(search_pipeline)

# Process a batch of queries
queries = ["What type of car is this?", "What landmark is shown in this photo?"]
images = [Image.open("path/to/car.jpg"), Image.open("path/to/landmark.jpg")]
message_histories = [[], []]  # Empty for single-turn conversations

responses = agent.batch_generate_response(queries, images, message_histories)
print(responses)
```

> **Pro Tip**: The RAG agent demonstrates how to combine vision-language models with external knowledge retrieval. It's particularly useful for queries requiring factual information beyond what's directly visible in the image.

---

## 🧰 Additional Resources

1. **[Submission Guidelines](../docs/submission.md)** – Explains how to structure your repo and push your agent for evaluation.
2. **[Agent Development Guide](../agents/README.md)** – Details how to create or modify an agent, including the `BaseAgent` interface.
3. **[Local Evaluation Script](../local_evaluation.py)** – Lets you test agents on the CRAG-MM dataset splits for quick iterations.

---

## 🔧 How to Switch Between Baselines

1. Open [`agents/user_config.py`](../agents/user_config.py).
2. Update the import and assignment:
   ```python
   from agents.rag_agent import SimpleRAGAgent
   UserAgent = SimpleRAGAgent
   ```
3. Run local evaluation:
   ```bash
   python local_evaluation.py --dataset-type single-turn --split validation --num-conversations 10 --display-conversations 3
   ```

---

## 🚀 Ready to Build Your Own?

1. **Pick a Baseline** that resonates with your approach.  
2. **Clone** it or **start fresh** with the [`BaseAgent`](../agents/base_agent.py).  
3. **Implement** your own approach - whether it's enhanced prompting, custom retrieval methods, or a specialized vision model.
4. **Test locally** with the evaluation script to ensure everything works as expected.
5. **Submit** your creation by following the instructions in [submission.md](../docs/submission.md)!  

---

**Enjoy hacking on these baselines, and may your answers be ever grounded in truth!** 🏆
