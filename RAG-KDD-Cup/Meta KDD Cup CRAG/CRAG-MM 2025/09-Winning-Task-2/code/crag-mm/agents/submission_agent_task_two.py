import os
import re
import time
from itertools import chain
from typing import Any, Dict, List
from urllib.parse import urlparse

import numpy as np
import vllm
from cragmm_search.search import UnifiedSearchPipeline
from PIL import Image

from agents.base_agent import BaseAgent
from crag_web_result_fetcher import WebSearchResult

# # Configuration constants
AICROWD_SUBMISSION_BATCH_SIZE = 16
VLLM_TENSOR_PARALLEL_SIZE = 1
VLLM_GPU_MEMORY_UTILIZATION = 0.8
MAX_MODEL_LEN = 8192
MAX_NUM_SEQS = 4
MAX_GENERATION_TOKENS = 75

NUM_WEB_SEARCH_QUERIES = 8
TOPK_WEB_SEARCH = 4
MAX_WEB_SEARCH_RESULTS = 12
TOPK_IMAGE_SEARCH = 4

CONTEXT_SCORE_TH = 0.6
IMG_SEARCH_SCORE_TH = 0.725
ENTITY_DETECTION_SCORE_TH = 0.8
MAX_ENTITY_QUERIES = 5

MIN_CONTEXT_EGO = 0
MIN_CONTEXT_NON_EGO = 4
TOPK_CONTEXT = 8

# IDK_TH = 0.3
IDK_TH_EGO = 0.1658
IDK_TH_NON_EGO = 0.1658


def get_stats(nums, name='context relevance'):
    print(f"----\n{name} scores: (N={len(nums)}), mean: {np.mean(nums):.2f}, std: {np.std(nums):.2f}, median: {np.median(nums):.2f}")

def is_ego(image):
    if (image.size[0] == 960) and (image.size[1] == 1280):
        return True
    return False

def _sliding_patches_square(img: Image.Image, n: int, overlap: float):
    """Sliding square grids."""
    W, H = img.size
    side   = min(W, H) // n
    if side == 0:                                    # n too large
        return []
    stride = max(1, int(side * (1 - overlap)))

    return [
        img.crop((x, y, x + side, y + side))
        for y in range(0, H - side + 1, stride)
        for x in range(0, W - side + 1, stride)
    ]

def _coarse_endcap_patches(img: Image.Image):
    W, H = img.size
    side = min(W, H)               # square side length

    if H > W:                      # ── portrait ───────────────────────────────
        y_top    = 0
        y_mid    = (H - side) // 2
        y_bottom = H - side
        boxes = [
            (0,        y_top,    W,        y_top + side),    # top
            (0,        y_mid,    W,        y_mid + side),    # middle
            (0,        y_bottom, W,        y_bottom + side)  # bottom
        ]

    elif W > H:                    # ── landscape ─────────────────────────────
        x_left   = 0
        x_mid    = (W - side) // 2
        x_right  = W - side
        boxes = [
            (x_left,  0, x_left  + side, H),                 # left
            (x_mid,   0, x_mid   + side, H),                 # middle
            (x_right, 0, x_right + side, H)                  # right
        ]

    else:                          # ── square ────────────────────────────────
        boxes = [(0, 0, W, H)]

    return [img.crop(b) for b in boxes]

def generate_multiscale_patches(
    img: Image.Image,
    grids   = ((1, 0.1), (1, 0.2), (1, 0.3), (1, 0.4)),    # (n, overlap) pairs
    add_endcaps: bool = True,
    keep_original: bool = True,
):
    """
    Return a flat list of PIL.Image patches combining:
      • optional original
      • optional coarse end-caps
      • multi-scale sliding grids
    Duplicate boxes (identical coords) are collapsed.
    """
    patches = []

    if keep_original:
        patches.append(img)

    if add_endcaps:
        patches.extend(_coarse_endcap_patches(img))

    for n, ov in grids:
        patches.extend(_sliding_patches_square(img, n, ov))

    return patches


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

def get_idk_prob(logprobs):
    i_logit = -100.0

    for _, logprob_obj in logprobs.items():
        token_str = logprob_obj.decoded_token

        if token_str.lower().strip() == "i":
            i_logit = logprob_obj.logprob
            break
    idk_prob = np.exp(i_logit)
    return idk_prob

def flatten_entity_attributes(attributes, prefix: str = "", max_words: int = 256, max_attrs: int = 32):
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

def encode_entity(entity):
    lines = []
    name = entity.get("entity_name")
    if name:
        lines.append(f"Entity Name: {name}")

    attributes = entity.get("entity_attributes") or {}
    lines.extend(flatten_entity_attributes(attributes))

    flat_snippet = "\n".join(lines).strip()

    return flat_snippet

def encode_image_search_result(result, max_entities=3):
    entities = result.get("entities", [])[:max_entities]

    enc = []
    for entity in entities:
        r = encode_entity(entity)
        enc.append(r)
    return "\n\n".join(enc)

def extract_search_queries(text, num_search_queries=3):
    parts = re.split(r'\n*1\.\s*', text, maxsplit=1)
    
    if len(parts) < 2:
        return []

    numbered_block = "1. " + parts[1]

    pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|\Z)'
    matches = re.findall(pattern, numbered_block, re.DOTALL)

    results = [m[1].strip() for m in matches[:num_search_queries]]
    results = [r.split("\n\n")[0] for r in results]
    results = [r.replace("**", "").strip() for r in results]
    
    return results

def url_to_breadcrumb(url: str, *, drop_single_label_tlds=("com",)) -> str:
    try:
        parsed = urlparse(url)
    
        # ---- host --------------------------------------------------------------
        host = parsed.hostname or ""
        host = re.sub(r"^www\.", "", host, flags=re.I)        # remove leading www.
        host_parts = host.split(".")
    
        # strip single-label TLDs like ".com", ".net" (configurable)
        if (
            len(host_parts) == 2                    # e.g. "example" + "com"
            and host_parts[-1] in drop_single_label_tlds
        ):
            host = host_parts[0]
    
        # ---- path --------------------------------------------------------------
        path_parts = [p for p in parsed.path.lstrip("/").split("/") if p]
        if path_parts:                               # remove extension on last part
            root, _ = os.path.splitext(path_parts[-1])
            path_parts[-1] = root or path_parts[-1]
    
        # ---- breadcrumb --------------------------------------------------------
        return " > ".join([host, *path_parts]) if path_parts else host
    except Exception as e:
        print(e)
        return url

def format_instruction(instruction, query, doc, max_doc_chars=3000):
    if len(doc) > max_doc_chars:
        doc = doc[:max_doc_chars] + "..."
    output = "<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}".format(instruction=instruction,query=query, doc=doc)
    return output

def get_ranker_input_text(query, doc):
    task = 'Determine whether the document is relevant to the query.'
    prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
    suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

    pair = format_instruction(task, query, doc)
    text = f"{prefix}{pair}{suffix}"
    return text

class CragAgent(BaseAgent):
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
        model_name: str = "rbiswasfc/aicrowd-kddcup-v9",
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

        self.context_relevance_scores = []
        
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
            limit_mm_per_prompt={
                "image": 1 
            } # In the CRAG-MM dataset, every conversation has at most 1 image
        )
        self.tokenizer = self.llm.get_tokenizer()
        
        print("Models loaded successfully")

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


    def crop_and_search(self, img, top_k, score_th=0.75):
        all_regions = generate_multiscale_patches(img)[:32]

        candidates = self.search_pipeline(all_regions, k=top_k)
        candidates = list(chain(*candidates))
        candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)

        result = []
        seen = set()
        first_result = None
        
        for c in candidates:
            score = c['score']
            name = None
            
            try:
                name = [e['entity_name'] for e in c['entities']][0]
                ent_repr = encode_image_search_result(c)
            except Exception as e:
                print(e)
                continue
                
            if name:
                if ent_repr not in seen:
                    this_result = (name, round(score, 4), ent_repr)
                    if score > score_th:
                        result.append(this_result)

                    if first_result is None:
                        first_result = this_result

                    seen.add(ent_repr)

        if len(result) == 0:
            return [first_result]

        return result[:top_k]
    def batch_perform_image_search(self, images, top_k=5):
        img_search_results = []

        for this_image in images:
            results = self.crop_and_search(this_image, top_k=top_k, score_th=IMG_SEARCH_SCORE_TH)
            img_search_results.append(results)
        
        return img_search_results

    def format_conversation_summary_only(self, history):
        user_questions = [entry["content"] for entry in history if entry["role"] == "user"]
        if user_questions:
            summary = "These are the earlier questions for context:\n"
            summary += "\n".join([f"{i+1}. {q}" for i, q in enumerate(user_questions)])
            summary += "\n\nNow I will ask a new question."
        else:
            summary = "Now I will ask a new question."
        return summary


    def batch_generate_web_queries(self, images, queries, num_search_queries=3):
        """
        Generate web search queries for a batch of images and questions.
        This method efficiently processes all images in a single batch call to the model, resulting in better performance compared to sequential processing.
        """
        
        inputs = []
        for image, query in zip(images, queries):
            prompt1 = f"""You will be shown an image and a question about that image. Your task is to generate {num_search_queries} short, diverse and effective web search queries that a person could type into a search engine (like Google) to find information that would help answer the question.
Each query should explore a **different** angle or approach to maximize coverage. The search engine will NOT see the image. So your search queries must be based only on what *you* can observe or infer from the image and the question — not something the search engine can figure out from the image itself.
Do not answer the question. Do not explain anything. Just return {num_search_queries} search queries as a numbered list. Be specific and concise in the queries. Focus on retrieving information that would be helpful to understand the image or answer the question."""

            prompt2 = f"""\n\nQuestion: {query}
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
        
        outputs = self.llm.generate(inputs, sampling_params=vllm.SamplingParams(temperature=0.1, top_p=0.9, max_tokens=128, skip_special_tokens=True), use_tqdm=False)

        queries = [output.outputs[0].text.strip() for output in outputs]
        queries = [extract_search_queries(s, num_search_queries=num_search_queries) for s in queries]

        return queries

    def batch_perform_web_search(self, batch_web_search_queries, search_k=8, top_k=16):
        search_results_batch = []
        
        for i, search_queries in enumerate(batch_web_search_queries):
            results = []
            for sq in search_queries:
                hits = self.search_pipeline(sq, k=search_k)
                for rank, hit in enumerate(hits):
                    hit['rank'] = rank
                    hit['query'] = sq
                    hit['breadcrumb'] = url_to_breadcrumb(hit['page_url'])
                    results.append(hit)
            
            results.sort(key=lambda x: x['score'], reverse=True)
            seen_enc = set()
            filtered_results = []            
            
            for result in results:
                result = WebSearchResult(result)
                snippet = result.get('page_snippet', '').strip()
                score = result.get('score', 0)
                query = result.get('query', '')
                page_name = result.get('page_name', '').strip()
                page_breadcrumb = result.get('breadcrumb', '').strip()
                page_enc = f"{page_breadcrumb}\n{page_name}\n{snippet}"
                
                
                if page_enc not in seen_enc:
                    # if len(snippet.strip()) > 0:
                    seen_enc.add(page_enc)
                    filtered_results.append((score, page_enc, query))
            
            filtered_results.sort(reverse=True, key=lambda x: x[0])
            search_results_batch.append(filtered_results[:top_k])
            
        return search_results_batch

    def _safe_truncate_prompt(self, messages, image, max_tokens, 
            base_prefix = "\n\nHere is some additional information that may help you answer:\n\n"):
        """
        Truncate RAG context in messages to fit within max_tokens.
        Prioritizes highest-score snippets and avoids duplicates.
        """

        tokenizer = self.tokenizer
        
        # Initial formatting
        formatted = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=True)
        if len(formatted) <= max_tokens:
            return tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
    
        # Locate RAG context
        context_index = None
        for i, m in enumerate(messages):
            if isinstance(m['content'], str) and m['content'].startswith(base_prefix):
                context_index = i
                break
        if context_index is None:
            print(f"No RAG context to truncate. Prompt: {messages}")
    
        # Extract snippets from current message
        original_context = messages[context_index]["content"]
        snippets = re.findall(r"\[Info \d+\](.*?)(?=\n\[Info|\Z)", original_context, re.DOTALL)
        snippets = [s.strip() for s in snippets]
    
        # Try incrementally adding snippets
        new_snippets = []
        for idx, snippet in enumerate(snippets):
            new_snippets.append(f"[Info {idx+1}] {snippet}\n\n")
            content = base_prefix + "".join(new_snippets)
            messages[context_index]["content"] = content
            formatted = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=True)
            if len(formatted) > max_tokens:
                new_snippets.pop()
                break
    
        messages[context_index]["content"] = base_prefix + "".join(new_snippets)
        return tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)

    def prepare_rag_enhanced_inputs(self, queries, images, message_histories, contexts):
        inputs = []
        QA_SYSTEM_PROMPT = """Answer the question factually. Instructions:
- Be specific and avoid assumptions
- Answer based only on what you can directly observe in the image
- Use additional context only if it's directly relevant and increases confidence
- If uncertain or the image doesn't contain the requested information, say "I don't know"

Provide a direct, factual answer in 1 sentence. If unsure, just say "I don't know" rather than guessing."""
        
        for query, image, message_history, context in zip(queries, images, message_histories, contexts):
            if context:
                context = [f"[Info {i+1}] {ctx}" for i, ctx in enumerate(context)]
                context = "\n\n".join(context)

            context = f"\n\nHere is some additional information that may help you answer:\n\n{context}"

            messages = [{"role": "system", "content": QA_SYSTEM_PROMPT}]

            if message_history:
                history_summary = self.format_conversation_summary_only(message_history)
                messages.append({"role": "user", "content": history_summary})

            messages.append({"role": "user", "content": context})
            messages.append({"role": "user", "content": [{"type": "image"}]})
            messages.append({"role": "user", "content": f"Question: {query}"})

            formatted_prompt = self._safe_truncate_prompt(messages, image, max_tokens=MAX_MODEL_LEN-128)
            
            inputs.append({"prompt": formatted_prompt, "multi_modal_data": {"image": image}})

        return inputs

    def get_rerank_scores(self, query, image, message_history, contexts):
        RANKER_SYSTEM_PROMPT = """Determine whether the provided context contains sufficient information to answer the given question about the image.

        Instructions:
        - Examine both the image and the additional context provided
        - Answer "Yes" if the context contains enough relevant information to answer the question accurately
        - Answer "No" if the context is insufficient, irrelevant, or contradicts what's visible in the image
        - Focus on whether the context helps answer the specific question asked
        - Consider the context as supplementary to what you can observe in the image

        Respond with only "Yes" or "No"."""
        inputs = []

        for context in contexts:
            context = f"\n\nAdditional Context:\n\n{context}"

            messages = [{"role": "system", "content": RANKER_SYSTEM_PROMPT}]
            if message_history:
                messages = messages + message_history
            messages.append({"role": "user", "content": context})
            messages.append({"role": "user", "content": [{"type": "image"}]})
            messages.append({"role": "user", "content": f"Question: {query}. Does the additional context offer enough information to answer the quesiton? (Yes/No)"})

            formatted_prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
            inputs.append({"prompt": formatted_prompt, "multi_modal_data": {"image": image}})

        outputs = self.llm.generate(inputs, sampling_params=vllm.SamplingParams(temperature=0.0, top_p=0.9, max_tokens=1, skip_special_tokens=True, logprobs=20))

        yes_probs = []
        for output in outputs:
            logprobs = output.outputs[0].logprobs[0]
            yes_prob = get_yes_prob(logprobs)
            yes_probs.append(yes_prob)

        self.context_relevance_scores.extend(yes_probs)
        get_stats(self.context_relevance_scores, name='Context Relevance')

        return yes_probs

    def batch_generate_response(
        self,
        queries: List[str],
        images: List[Image.Image],
        message_histories: List[List[Dict[str, Any]]],
    ) -> List[str]:
        """
        Generate RAG-enhanced responses for a batch of queries with associated images.
        
        This method implements a complete RAG pipeline with efficient batch processing:
        1. First batch-summarize all images to generate search terms
        2. Then retrieve relevant information using these terms
        3. Finally, generate responses incorporating the retrieved context
        
        Args:
            queries (List[str]): List of user questions or prompts.
            images (List[Image.Image]): List of PIL Image objects, one per query.
                The evaluator will ensure that the dataset rows which have just
                image_url are populated with the associated image.
            message_histories (List[List[Dict[str, Any]]]): List of conversation histories,
                one per query. Each history is a list of message dictionaries with
                'role' and 'content' keys in the following format:
                
                - For single-turn conversations: Empty list []
                - For multi-turn conversations: List of previous message turns in the format:
                  [
                    {"role": "user", "content": "first user message"},
                    {"role": "assistant", "content": "first assistant response"},
                    {"role": "user", "content": "follow-up question"},
                    {"role": "assistant", "content": "follow-up response"},
                    ...
                  ]
                
        Returns:
            List[str]: List of generated responses, one per input query.
        """
        print(f"Processing batch of {len(queries)} queries with RAG")

        start_time = time.time()

        image_search_results_batch = self.batch_perform_image_search(images, top_k=TOPK_IMAGE_SEARCH)

        #--------------------------------
        for i, image_results in enumerate(image_search_results_batch):
            print(f"Example {i} Image Search Results:")
            for name, score, content in image_results:
                print(f"{name:<64} -> {score:.2f} (# chars: {len(content)})")
            print("-"*100)
        #--------------------------------

        entity_names_batch = []
        for i, image_search_results in enumerate(image_search_results_batch):
            ex_names = []
            for name, score, _ in image_search_results:
                if score > ENTITY_DETECTION_SCORE_TH:
                    ex_names.append(name.strip())
            entity_names_batch.append(ex_names)

        #--------------------------------
        print("-"*100)
        for i, entity_names in enumerate(entity_names_batch):
            print(f"Example {i} Entity names for web search: {', '.join(entity_names)}")
        print("-"*100)
        #--------------------------------
        
        web_queries_batch = self.batch_generate_web_queries(images, queries, num_search_queries=NUM_WEB_SEARCH_QUERIES)
        
        # add additional web queries --
        for i, (query, wq) in enumerate(zip(queries, web_queries_batch)):
            if len(entity_names_batch[i]) > 0:
                ents = ", ".join(entity_names_batch[i])
                sq = f"{ents} : {query}"
                wq.append(sq)
        
        #--------------------------------
        for i, web_queries in enumerate(web_queries_batch):
            wq_str = "\n".join([f"{i+1}. {q}" for i, q in enumerate(web_queries)])
            print(f"Example {i} Web Queries:\n\n{wq_str}")
            print("-"*100)
        #--------------------------------   

        web_search_results_batch = self.batch_perform_web_search(web_queries_batch, search_k=TOPK_WEB_SEARCH, top_k=MAX_WEB_SEARCH_RESULTS)

        contexts_batch = []
        for i, (web_contexts, image_contexts) in enumerate(zip(web_search_results_batch, image_search_results_batch)):
            ex_contexts = []
            for rix, ctx in enumerate(web_contexts):
                score, content, _ = ctx
                ex_contexts.append({'kind': 'web', 'api_score': score, 'api_rank': rix+1, 'content': content})
            for rix, ctx in enumerate(image_contexts):
                name, score, content = ctx
                ex_contexts.append({'kind': 'image', 'api_score': score, 'api_rank': rix+1, 'content': content})
            contexts_batch.append(ex_contexts)

        # get rerank scores ---
        context_batch_with_scores = []
        for i, (query, image, message_history, contexts) in enumerate(zip(queries, images, message_histories, contexts_batch)):
            print(f"Ranking {i} of {len(queries)}")
            contents = [ctx['content'] for ctx in contexts]
            rerank_scores  = self.get_rerank_scores(query, image, message_history, contents)

            sorted_indices = np.argsort(rerank_scores)[::-1]
            ranks = np.empty_like(sorted_indices)
            ranks[sorted_indices] = np.arange(len(sorted_indices)) + 1 
            
            for ptr in range(len(contexts)):
                contexts[ptr]['rerank_score'] = rerank_scores[ptr]
                contexts[ptr]['rerank_rank'] = ranks[ptr]  # Now correctly assigns rank
                contexts[ptr]['combined_rank'] = contexts[ptr]['api_rank'] + contexts[ptr]['rerank_rank']
            context_batch_with_scores.append(contexts)

        # prepare RAG-enhanced inputs
        # strategy 1: just use top reranker scores to select contexts
        print("Strategy A: just use top reranker scores to select contexts")
        context_batch_a = []
        for i, contexts in enumerate(context_batch_with_scores):
            selected = []
            top_contexts = sorted(contexts, key=lambda x: x['rerank_rank'])

            ### MIN CONTEXT SETTING ###
            this_image = images[i]
            is_ego_image = is_ego(this_image)

            if is_ego_image:
                MIN_CONTEXT = MIN_CONTEXT_EGO
            else:
                MIN_CONTEXT = MIN_CONTEXT_NON_EGO
            print(f"Example {i} is EGO: {is_ego_image}, min_context: {MIN_CONTEXT}")
            ### MIN CONTEXT SETTING ###

            for ci, this_ctx in enumerate(top_contexts):
                if this_ctx['rerank_score'] >= CONTEXT_SCORE_TH or ci < MIN_CONTEXT: # keep at least MIN_CONTEXT contexts
                    selected.append(this_ctx)
            selected = selected[:TOPK_CONTEXT]
            context_batch_a.append([ctx['content'] for ctx in selected])

            #--------------------------------
            print(f"Example {i} Contexts A:")
            for ctx in selected:
                print(f"Kind: {ctx['kind']}, API Score: {ctx['api_score']:.2f}, Rerank Score: {ctx['rerank_score']:.2f}, Rerank Rank: {ctx['rerank_rank']}, API Rank: {ctx['api_rank']}, Combined Rank: {ctx['combined_rank']}, Content: {ctx['content'][:16]}...")
            print("-"*100)
            #--------------------------------

        # strategy 2: combined ranks to select contexts and keep top API context ---
        print("Strategy B: combined ranks to select contexts and keep top API context")
        context_batch_b = []
        for i, contexts in enumerate(context_batch_with_scores):
            selected = []
            top_contexts = sorted(contexts, key=lambda x: x['combined_rank'])

            ### MIN CONTEXT SETTING ###
            this_image = images[i]
            is_ego_image = is_ego(this_image)

            if is_ego_image:
                MIN_CONTEXT = MIN_CONTEXT_EGO
            else:
                MIN_CONTEXT = MIN_CONTEXT_NON_EGO
            ### MIN CONTEXT SETTING ###


            for ci, this_ctx in enumerate(top_contexts):
                if this_ctx['api_rank'] == 1:
                    selected.append(this_ctx) # just keep the top API context for both sources
                elif this_ctx['rerank_score'] >= CONTEXT_SCORE_TH or ci < MIN_CONTEXT: # keep at least MIN_CONTEXT contexts
                    selected.append(this_ctx)
            selected = selected[:TOPK_CONTEXT]
            context_batch_b.append([ctx['content'] for ctx in selected])

            #--------------------------------
            print(f"Example {i} Contexts B:")
            for ctx in selected:
                print(f"Kind: {ctx['kind']}, API Score: {ctx['api_score']:.2f}, Rerank Score: {ctx['rerank_score']:.2f}, Rerank Rank: {ctx['rerank_rank']}, API Rank: {ctx['api_rank']}, Combined Rank: {ctx['combined_rank']}, Content: {ctx['content'][:16]}...")
            print("-"*100)
            #--------------------------------

        ##########
        rag_inputs_a = self.prepare_rag_enhanced_inputs(queries, images, message_histories, context_batch_a)
        rag_inputs_b = self.prepare_rag_enhanced_inputs(queries, images, message_histories, context_batch_b)

        # Step 5: Generate responses using the batch of RAG-enhanced prompts
        print(f"Generating responses for {len(rag_inputs_a)} queries")
        outputs_a = self.llm.generate(
            rag_inputs_a,
            sampling_params=vllm.SamplingParams(
                temperature=0.0,
                top_p=0.9,
                max_tokens=MAX_GENERATION_TOKENS,
                skip_special_tokens=True,
                logprobs=20
            ),
            use_tqdm=False,
        )

        # outputs_b = self.llm.generate(
        #     rag_inputs_b,
        #     sampling_params=vllm.SamplingParams(
        #         temperature=0.0,
        #         top_p=0.9,
        #         max_tokens=MAX_GENERATION_TOKENS,
        #         skip_special_tokens=True,
        #         logprobs=20
        #     ),
        #     use_tqdm=False,
        # )

        # Extract and return the generated responses
        responses_a = [output.outputs[0].text for output in outputs_a]
        # responses_b = [output.outputs[0].text for output in outputs_b]
        responses_b = responses_a

        idk_probs_a = []
        for output in outputs_a:
            logprobs = output.outputs[0].logprobs[0]
            idk_prob = get_idk_prob(logprobs)
            idk_probs_a.append(idk_prob)

        # idk_probs_b = []
        # for output in outputs_b:
        #     logprobs = output.outputs[0].logprobs[0]
        #     idk_prob = get_idk_prob(logprobs)
        #     idk_probs_b.append(idk_prob)

        idk_probs_b = idk_probs_a


        # select final responses (based on lower idk prob) ---
        responses = []
        idk_probs = []
        for i, (response_a, response_b, idk_prob_a, idk_prob_b) in enumerate(zip(responses_a, responses_b, idk_probs_a, idk_probs_b)):
 
            if response_a != "I don't know": # if response_a is not "I don't know", use it
                responses.append(response_a)
                idk_probs.append(idk_prob_a)
            elif idk_prob_b < idk_prob_a: # else if response_b is more confident than response_a, use it
                responses.append(response_b)
                idk_probs.append(idk_prob_b)
            else:
                responses.append(response_a)
                idk_probs.append(idk_prob_a)

            #--------------------------------
            print(f"Example {i}")
            print(f"Response A: {response_a} (IDK prob: {idk_prob_a:.4f})")
            print(f"Response B: {response_b} (IDK prob: {idk_prob_b:.4f})")
            print(f"Selected: {responses[-1]} (IDK prob: {idk_probs[-1]:.4f})")
            print("-"*100)
            #--------------------------------  

        print(f"Successfully generated {len(responses)} responses")


        for i, (response, idk_prob) in enumerate(zip(responses, idk_probs)):
            print(f"(IDK prob: {idk_prob:.4f}) Response {i}: {response} ")

        # idk_th = 0.025
        # responses = [response if idk_prob < idk_th else "I don't know" for response, idk_prob in zip(responses, idk_probs)]

        for i, (response, idk_prob) in enumerate(zip(responses, idk_probs)):
            image = images[i]
            is_ego_image = is_ego(image)
            if is_ego_image:
                idk_th = IDK_TH_EGO
            else:
                idk_th = IDK_TH_NON_EGO

            if idk_prob > idk_th:
                responses[i] = "I don't know"


        end_time = time.time()

        print(f"Time taken: {end_time - start_time:.2f} seconds")
        return responses
