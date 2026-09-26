import math
import os
import re
from typing import Any, Dict, List

import numpy as np
import torch
import vllm
from cragmm_search.search import UnifiedSearchPipeline
from PIL import Image
from transformers import OwlViTForObjectDetection, OwlViTProcessor

from agents.base_agent import BaseAgent
from crag_web_result_fetcher import WebSearchResult

# Parameters for the agent
AICROWD_SUBMISSION_BATCH_SIZE = 16
VLLM_TENSOR_PARALLEL_SIZE = 8 # 8xA100
VLLM_GPU_MEMORY_UTILIZATION = 0.85 
MAX_MODEL_LEN = 8192
MAX_NUM_SEQS = 128
MAX_GENERATION_TOKENS = 75
NUM_SEARCH_RESULTS = 5

NUM_SEARCH_OBJECTS = 2 # number of objects to search for in the image, used in owlvit
NUM_WEB_SEARCH_QUERIES = 3 # number of web search queries to generate
TOPK_WEB_SEARCH = 8  # number of web search results to return
TOPK_IMAGE_SEARCH = 5  # number of image search results to return


def get_yes_prob(logprobs):
    yes_logit = None
    no_logit = None

    for _, logprob_obj in logprobs.items():
        token_str = logprob_obj.decoded_token.strip().lower()

        if token_str.lower().strip() == "yes":
            if yes_logit is None:
                yes_logit = logprob_obj.logprob # get first yes logit
        elif token_str.lower().strip() == "no":
            if no_logit is None:
                no_logit = logprob_obj.logprob # get first no logit

    if yes_logit is None and no_logit is None:
        return 0.5
    elif yes_logit is None:
        return 0.0
    elif no_logit is None:
        return 1.0

    logits = np.array([yes_logit, no_logit])
    logits_max = np.max(logits)
    exp_logits = np.exp(logits - logits_max)
    normalized_scores = exp_logits / np.sum(exp_logits)

    yes_prob = normalized_scores[0]
    return yes_prob


def flatten_entity_attributes(attributes, prefix: str = "", max_words: int = 64, max_attrs: int = 64):
    """
    Flattens nested entity attributes into `"key.subkey: value"` lines.
    """

    def _truncate(s: str) -> str:
        words = s.strip().split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."
        return " ".join(words)

    if not isinstance(attributes, dict):
        label = prefix.strip(".") or "value"
        return [f"{label}: {_truncate(str(attributes))}"]

    lines = []

    for key, value in attributes.items():
        if len(lines) >= max_attrs:
            break

        full_key = f"{prefix}{key}" if prefix else key

        if isinstance(value, dict):
            remaining = max_attrs - len(lines)
            if remaining:
                child_lines = flatten_entity_attributes(value, prefix=f"{full_key}.", max_words=max_words, max_attrs=remaining)
                lines.extend(child_lines)

        elif isinstance(value, list) and value:
            truncated_items = [_truncate(item) if isinstance(item, str) else str(item) for item in value]
            lines.append(f"{full_key}: {', '.join(truncated_items)}")

        elif isinstance(value, str):
            lines.append(f"{full_key}: {_truncate(value)}")

        elif value is not None:
            lines.append(f"{full_key}: {value}")

    return lines[:max_attrs]

def extract_search_queries(text, num_search_queries=3):
    parts = re.split(r'\n*1\.\s*', text, maxsplit=1)
    
    if len(parts) < 2:
        return []

    numbered_block = "1. " + parts[1]

    pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|\Z)'
    matches = re.findall(pattern, numbered_block, re.DOTALL)

    results = [m[1].strip() for m in matches[:num_search_queries]]
    
    return results

class CragAgentDataGen(BaseAgent):
    """
    SimpleRAGAgent demonstrates all the basic components you will need to create your 
    RAG submission for the CRAG-MM benchmark.
    Note: This implementation is not tuned for performance, and is intended for demonstration purposes only.
    
    This agent enhances responses by retrieving relevant information through a search pipeline
    and incorporating that context when generating answers. It follows a two-step approach:
    1. First, batch-summarize all images to generate effective search terms
    2. Then, retrieve relevant information and incorporate it into the final prompts
    
    The agent leverages batched processing at every stage to maximize efficiency.
    
    Note:
        This agent requires a search_pipeline for RAG functionality. Without it,
        the agent will raise a ValueError during initialization.
    
    Attributes:
        search_pipeline (UnifiedSearchPipeline): Pipeline for searching relevant information.
        model_name (str): Name of the Hugging Face model to use.
        max_gen_len (int): Maximum generation length for responses.
        llm (vllm.LLM): The vLLM model instance for inference.
        tokenizer: The tokenizer associated with the model.
    """

    def __init__(
        self,
        search_pipeline: UnifiedSearchPipeline, 
        model_name: str = "meta-llama/Llama-3.2-11B-Vision-Instruct", 
        max_gen_len: int = 64
    ):
        """
        Initialize the RAG agent with the necessary components.
        
        Args:
            search_pipeline (UnifiedSearchPipeline): A pipeline for searching web and image content.
                Note: The web-search will be disabled in case of Task 1 (Single-source Augmentation) - so only image-search can be used in that case.
                      Hence, this implementation of the RAG agent is not suitable for Task 1 (Single-source Augmentation).
            model_name (str): Hugging Face model name to use for vision-language processing.
            max_gen_len (int): Maximum generation length for model outputs.
            
        Raises:
            ValueError: If search_pipeline is None, as it's required for RAG functionality.
        """
        super().__init__(search_pipeline)
        
        if search_pipeline is None:
            raise ValueError("Search pipeline is required for RAG agent")
            
        self.model_name = model_name
        self.max_gen_len = max_gen_len
        
        self.initialize_models()
        
    def initialize_models(self):
        """
        Initialize the vLLM model and tokenizer with appropriate settings.
        
        This configures the model for vision-language tasks with optimized
        GPU memory usage and restricts to one image per prompt, as 
        Llama-3.2-Vision models do not handle multiple images well in a single prompt.
        
        Note:
            The limit_mm_per_prompt setting is critical as the current Llama vision models
            struggle with multiple images in a single conversation.
            Ref: https://huggingface.co/meta-llama/Llama-3.2-11B-Vision-Instruct/discussions/43#66f98f742094ed9e5f5107d4
        """
        print(f"Initializing {self.model_name} with vLLM...")
        
        # Initialize the model with vLLM
        self.llm = vllm.LLM(
            self.model_name,
            tensor_parallel_size=VLLM_TENSOR_PARALLEL_SIZE, 
            gpu_memory_utilization=VLLM_GPU_MEMORY_UTILIZATION, 
            max_model_len=MAX_MODEL_LEN,
            max_num_seqs=MAX_NUM_SEQS,
            trust_remote_code=True,
            dtype="bfloat16",
            enforce_eager=True,
            limit_mm_per_prompt={"image": 1},
            enable_prefix_caching=True
        )
        self.tokenizer = self.llm.get_tokenizer()
        
        print("Models loaded successfully")

        self.owlvit_processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
        self.owlvit_model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")
        self.owlvit_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.owlvit_model.to(self.owlvit_device)

    def get_batch_size(self) -> int:
        """
        Determines the batch size used by the evaluator when calling batch_generate_response.
        
        The evaluator uses this value to determine how many queries to send in each batch.
        Valid values are integers between 1 and 16.
        
        Returns:
            int: The batch size, indicating how many queries should be processed together 
                 in a single batch.
        """
        return AICROWD_SUBMISSION_BATCH_SIZE


    def batch_generate_web_queries(self, images, queries, num_search_queries=3):
        """
        Generate web search queries for a batch of images and questions.
        This method efficiently processes all images in a single batch call to the model, resulting in better performance compared to sequential processing.
        """
        
        inputs = []
        for image, query in zip(images, queries):
            prompt1 = f"""You will be shown an image and a question about that image.

            Your task is to generate {num_search_queries} short, diverse and effective web search queries that a person could type into a search engine (like Google) to find information that would help answer the question.

            Each query should explore a **different** angle or approach to maximize coverage.
            
            The search engine will NOT see the image. So your search queries must be based only on what *you* can observe or infer from the image and the question — not something the search engine can figure out from the image itself.

            Do not answer the question. Do not explain anything. Just return {num_search_queries} search queries as a numbered list.

            Be specific and concise in the queries. Focus on retrieving information that would be helpful to understand the image or answer the question.

            Image:"""

            prompt2 = f"""
            Question: {query}

            Now provide {num_search_queries} useful search queries."""

            messages = []
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt1},
                        {"type": "image"},
                        {"type": "text", "text": prompt2}
                    ],
                }
            )

            formatted_prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
            inputs.append({"prompt": formatted_prompt, "multi_modal_data": {"image": image}})

        if len(inputs)==0: 
            return [[] for _ in images]
        
        outputs = self.llm.generate(inputs, sampling_params=vllm.SamplingParams(temperature=0.1, top_p=0.9, max_tokens=256, skip_special_tokens=True))

        queries = [output.outputs[0].text.strip() for output in outputs]
        queries = [extract_search_queries(s, num_search_queries=num_search_queries) for s in queries]

        return queries

    def batch_generate_search_objects(self, images, queries, num_search_objects=3):
        inputs = []
        
        for i, (image, query) in enumerate(zip(images, queries)):
            prompt1 = f"""You will be shown an image and a question about that image.
            Your task is to list up to {num_search_objects} distinct objects or clearly visible regions that should be cropped from the image and submitted to an image-based visual search system to help answer the question.
            
            IMPORTANT:
            - Only suggest things that are visible and clearly identifiable in the image.
            - Each suggestion should be a short noun phrase, no more than 4 words.
            - Must be relevant to answering the specific question asked
            - Do not include abstract parts like "nutrition label" or vague descriptions like "object on the left".
            - Avoid phrases with "with", "that has", or other relational descriptions.
            - Think like a visual detection model: what simple things can be seen and cropped?
            - Prioritize regions containing:
                • Text, labels, logos, or brand marks
                • Unique identifying features or patterns
                • Objects central to the question's focus
                • Distinctive visual elements that could yield search results
                
            Do not answer the question. Do not explain anything. Just return up to {num_search_objects} short object phrases as a numbered list.
            Image:"""
            prompt2 = f"""
            Question: {query}
            Now list {num_search_objects} clearly visible things to crop from the image that would help answer this specific question ({query}). Use short object phrases.
            """

            messages = []
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt1},
                        {"type": "image"},
                        {"type": "text", "text": prompt2}
                    ],
                }
            )

            formatted_prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)

            inputs.append({"prompt": formatted_prompt, "multi_modal_data": {"image": image}})

        if len(inputs)==0: 
            return [[] for _ in images]
        
        outputs = self.llm.generate(
            inputs,
            sampling_params=vllm.SamplingParams(
                temperature=0.1,
                top_p=0.9,
                max_tokens=256,  
                skip_special_tokens=True
            )
        )

        search_objects = [output.outputs[0].text.strip() for output in outputs]
        search_objects = [extract_search_queries(s, num_search_queries=num_search_objects) for s in search_objects]

        return search_objects


    def batch_perform_web_search(self, batch_web_search_queries, top_k=16):
        search_results_batch = []
        
        for i, search_queries in enumerate(batch_web_search_queries):
            results = []
            for sq in search_queries:
                hits = self.search_pipeline(sq, k=top_k)
                for rank, hit in enumerate(hits):
                    hit['rank'] = rank
                    hit['query'] = sq
                    results.append(hit)
            
            seen_snippets = set()
            filtered_results = []
            
            # sort by rank, for query attribution in case of same snippet is returned from multiple queries
            results.sort(key=lambda x: x['rank'])
            
            for result in results:
                result = WebSearchResult(result)
                snippet = result.get('page_snippet', '').strip()
                score = result.get('score', 0)
                query = result.get('query', '')
                
                if snippet and snippet not in seen_snippets:
                    seen_snippets.add(snippet)
                    filtered_results.append((score, snippet, query))
            
            filtered_results.sort(reverse=True, key=lambda x: x[0])
            search_results_batch.append(filtered_results)
            
        return search_results_batch


    def batch_perform_image_search(self, images, object_phrases, top_k=5):
        img_search_results = []
        
        for i, (these_objects, this_image) in enumerate(zip(object_phrases, images)):
            cropped_images = [("original", this_image)]
            
            if len(these_objects) > 0:
                if isinstance(this_image, np.ndarray):
                    if this_image.ndim == 2:
                        this_image = np.stack([this_image] * 3, axis=-1)  # Shape becomes (H, W, 3)
                    this_image = Image.fromarray(this_image.astype(np.uint8))

                if this_image.mode != "RGB":
                    this_image = this_image.convert("RGB")

                inputs_owl = self.owlvit_processor(text=[these_objects], images=this_image, return_tensors="pt", padding=True, truncation=True) 
                inputs_owl = {k: v.to(self.owlvit_device) for k, v in inputs_owl.items()}
                with torch.no_grad():
                    outputs = self.owlvit_model(**inputs_owl)

                target_sizes = torch.Tensor([this_image.size[::-1]])
                results = self.owlvit_processor.post_process_grounded_object_detection(outputs, threshold=0.01, target_sizes=target_sizes)

                boxes, scores, labels = results[0]["boxes"], results[0]["scores"], results[0]["labels"]
                for label_id in range(len(these_objects)):
                    filtered = [(b, s) for b, s, l in zip(boxes, scores, labels) if l == label_id]
                    if filtered:
                        box, score = sorted(filtered, key=lambda x: x[1], reverse=True)[0]
                        box = [int(x) for x in box.tolist()]
                        crop = this_image.crop(box)
                        cropped_images.append((these_objects[label_id], crop))

            results = []
            for label, img in cropped_images:
                hits = self.search_pipeline(img, k=top_k)
                for rank, hit in enumerate(hits):
                    hit['rank'] = rank
                    hit['query'] = label
                    results.append(hit)

            # deduplication
            results.sort(key=lambda x: x['rank'])

            seen_idxs = set()
            filtered_results = []

            for result in results:
                score = result.get("score", 0)
                entities = result.get("entities", [])
                query = result.get("query", "unknown")

                for entity in entities:
                    lines = []
                    name = entity.get("entity_name")
                    if name:
                        lines.append(f"Entity Name: {name}")
                    attributes = entity.get("entity_attributes") or {}
                    lines.extend(flatten_entity_attributes(attributes))
                    flat_snippet = "\n".join(lines).strip()

                if flat_snippet and result['index'] not in seen_idxs:
                    seen_idxs.add(result['index'])
                    filtered_results.append((score, flat_snippet, query))

            filtered_results.sort(reverse=True, key=lambda x: x[0])
            img_search_results.append(filtered_results)
        
        return img_search_results


    def prepare_agent_inputs(self, queries, images, message_histories, web_contexts, image_contexts, answers):
        inputs = []
        meta_info = []
        groundedness_inputs = []

        SYSTEM_PROMPT = """Please answer the question based on the provided context.

        Instructions:
        - Be specific and avoid assumptions
        - Answer based only on what you can directly observe in the image
        - Use the provided additional context to help answer the question"""
        
        SYSTEM_PROMPT_GROUNDEDNESS = """Evaluate whether the given answer is accurate based ONLY on what is visible in the image and provided context.

Instructions:
- Compare the answer's claims against observable evidence in the image
- Mark as "No" if the answer contains any factual errors, unsupported claims, or contradictions
- Mark as "Yes" only if all statements in the answer can be verified from the image/context
- Ignore information you know but cannot see in the image
- If the answer makes claims beyond what's visible in the image or provided context, mark as "No"

Respond with only "Yes" or "No".
        """
        
        for eid, query, image, message_history, web_context, image_context, answer in zip(range(len(queries)), queries, images, message_histories, web_contexts, image_contexts, answers):
            all_context = web_context + image_context
            n_web_search = len(web_context)

            for cid, (score, content, search_string) in enumerate(all_context):
                this_context = f"\n\nHere is some additional information that may help you answer:\n\n{content}\n\n"

                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [{"type": "image"}]}
                ]

                if message_history:
                    messages = messages + message_history

                messages.append({"role": "user", "content": this_context})
                messages.append({"role": "user", "content": f"{query}"})

                formatted_prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
            
                inputs.append({"prompt": formatted_prompt, "multi_modal_data": {"image": image}})
                meta_info.append({"example_idx": eid, "search_string": search_string, "search_content": content, "score": score, "is_web_search": True if cid < n_web_search else False})

                # groundedness check ----
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT_GROUNDEDNESS},
                    {"role": "user", "content": [{"type": "image"}]}
                ]

                if message_history:
                    messages = messages + message_history

                messages.append({"role": "user", "content": this_context})
                messages.append({"role": "user", "content": f"Question: {query}\nAnswer: {answer}\n\nIs the answer correct based on the image and context? (Yes/No)"})

                formatted_prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
                groundedness_inputs.append({"prompt": formatted_prompt, "multi_modal_data": {"image": image}})

        return inputs, meta_info, groundedness_inputs

    def batch_generate_response(self, queries, images, message_histories, answers):

        web_queries_batch = self.batch_generate_web_queries(images, queries, num_search_queries=NUM_WEB_SEARCH_QUERIES)
        image_queries_batch = self.batch_generate_search_objects(images, queries, num_search_objects=NUM_SEARCH_OBJECTS)

        web_search_results_batch = self.batch_perform_web_search(web_queries_batch, top_k=TOPK_WEB_SEARCH)
        image_search_results_batch = self.batch_perform_image_search(images, image_queries_batch, top_k=TOPK_IMAGE_SEARCH)

        agent_inputs, meta_info, groundedness_inputs = self.prepare_agent_inputs(queries, images, message_histories, web_search_results_batch, image_search_results_batch, answers)

        outputs = self.llm.generate(
            agent_inputs,
            sampling_params=vllm.SamplingParams(
                temperature=0.1,
                top_p=0.9,
                max_tokens=MAX_GENERATION_TOKENS,
                skip_special_tokens=True
            )
        )
        
        responses = [output.outputs[0].text for output in outputs]

        # groundedness check ----
        groundedness_outputs = self.llm.generate(
            groundedness_inputs,
            sampling_params=vllm.SamplingParams(
                temperature=0.0,
                top_p=0.9,
                max_tokens=1,
                skip_special_tokens=True,
                logprobs=20,
            )
        )

        yes_probs = []
        for output in groundedness_outputs:
            logprobs = output.outputs[0].logprobs[0]
            yes_prob = get_yes_prob(logprobs)
            yes_probs.append(yes_prob)

        # combine responses with meta_info
        to_return = []

        for i, response in enumerate(responses):
            metadata = meta_info[i]
            yes_prob = yes_probs[i]
            this_entry = {
                "example_idx": metadata["example_idx"],
                "query": queries[metadata["example_idx"]],
                "image": images[metadata["example_idx"]],
                "message_history": message_histories[metadata["example_idx"]],
                "answer": answers[metadata["example_idx"]],
                "predicted_answer": response,
                "search_string": metadata["search_string"],
                "search_content": metadata["search_content"],
                "is_web_search": metadata["is_web_search"],
                "context_relevance": yes_prob,
            }
            to_return.append(this_entry)

        return to_return
