import argparse
import base64
import io
import json
import os
import sys
import time
import traceback

import requests
from datasets import load_dataset
from PIL import Image
from tqdm import tqdm

# Add parent directory to path for utils import
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from utils import download_image_url


def get_llama_output(prompt, image, model="meta/llama-4-maverick-17b-128e-instruct", max_tokens=256, temperature=0.1, top_p=0.95, seed=None, max_retries=5):
    
    model2url = {
        "meta/llama-3.2-11b-vision-instruct": "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions",
        "meta/llama-3.2-90b-vision-instruct": "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-90b-vision-instruct/chat/completions",
        "meta/llama-4-scout-17b-16e-instruct": "https://integrate.api.nvidia.com/v1/chat/completions",
        "meta/llama-4-maverick-17b-128e-instruct": "https://integrate.api.nvidia.com/v1/chat/completions",
    }

    invoke_url = model2url[model]

    max_size = (1024, 1024)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)

    image_b64 = base64.b64encode(buffer.getvalue()).decode()

    stream = False
    headers = {
        "Authorization": f"Bearer {os.environ['NVDEV_ENDPOINT_KEY']}",
        "Accept": "text/event-stream" if stream else "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": f'{prompt} <img src="data:image/png;base64,{image_b64}" />'}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
        "seed": seed,
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(invoke_url, headers=headers, json=payload, timeout=60)
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                return response_json["choices"][0]["message"]["content"]
            else:
                print(f"API response missing choices (attempt {attempt + 1}): {response_json}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
        except Exception as e:
            print(f"API call failed (attempt {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
    
    raise Exception(f"Failed to get response after {max_retries} attempts")

def generate_query(image, query, num_search_queries=8, model="meta/llama-4-maverick-17b-128e-instruct"):
    
    prompt = f"""You will be shown an image and a question about that image.
Your task is to generate {num_search_queries} short, diverse and effective web search queries that a person could type into a search engine (like Google) to find information that would help answer the question.

Critical constraint: The search engine CANNOT see the image. You must include visual details in the queries.

Your mission: Generate queries that will return search results containing the answer to the question.

Process:
1. Unserstand the visual context and identify the possible subject(s) the question could be referring to
2. For each possible subject, create search queries that include subject specific keywords and aspects related to the question
3. Create queries for each plausible subject

Query optimization:
- Make each query short and self-contained (8-12 words)
- Distribute queries across different plausible interpretations from visual context and posed question
- Try to maximize answer retrieval possibility i.e. recall
- Avoid redundant phrasing and trivial re-orderig
- Use varied search approaches

Do not answer the question. Just return {num_search_queries} search queries as a numbered list.

Question: {query}

Now, generate search strings that will retrieve the ANSWER to this question. The search engine cannot see the image - include visual details.
Provide {num_search_queries} diverse search queries."""

    web_queries = get_llama_output(prompt, image, model=model, max_tokens=128, temperature=0.2)
    
    return web_queries

if __name__ == "__main__":
    # Check for required environment variable
    if 'NVDEV_ENDPOINT_KEY' not in os.environ:
        print("Error: NVDEV_ENDPOINT_KEY environment variable not set")
        sys.exit(1)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_idx", type=int, default=0, help="Start index of the dataset")
    parser.add_argument("--end_idx", type=int, default=2000, help="End index of the dataset")
    parser.add_argument("--output_dir", type=str, default="data/kddcup25_synthetic/query_writing", help="Output directory")
    args = parser.parse_args()

    dataset_type = "single-turn"
    dataset_split = "public_test"
    repo_name = f"crag-mm-2025/crag-mm-{dataset_type}-public"
    dataset = load_dataset(repo_name, revision="v0.1.2")[dataset_split]

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    start_idx = args.start_idx
    end_idx = args.end_idx
    end_idx = min(end_idx, len(dataset))
    
    print(f"Processing indices {start_idx} to {end_idx} from dataset of size {len(dataset)}")

    if start_idx >= len(dataset):
        print(f"Start index {start_idx} >= dataset size {len(dataset)}, nothing to process")
        sys.exit(0)

    dataset = dataset.select(range(start_idx, end_idx))
    print(f"Selected {len(dataset)} examples to process")

    # Fix progress bar to match actual iteration
    pbar = tqdm(dataset, desc=f"Processing {start_idx}-{end_idx}")
    
    processed = 0
    saved = 0
    
    for example in pbar:
        try:
            image = example['image']
            image_url = example['image_url']
            query = example['turns']['query'][0]

            if image_url and len(image_url.strip()) > 0:
                image_path = download_image_url(image_url)
                image = Image.open(image_path)
                image = image.convert("RGB")
            else:
                # Use the provided image if no URL
                pass

            web_queries = generate_query(image, query, num_search_queries=8, model="meta/llama-4-maverick-17b-128e-instruct")

            session_id = example['session_id']
            interaction_id = example['turns']['interaction_id'][0]
            this_example = {
                "session_id": session_id,
                "interaction_id": interaction_id,
                "web_queries": web_queries,
            }
            
            # save to a folder as json
            save_path = os.path.join(output_dir, f"{session_id}_{interaction_id}.json")
            with open(save_path, "w") as f:
                json.dump(this_example, f)
            
            print(f"Saved to {save_path}")
            saved += 1
            
        except Exception as e:
            print(f"Error processing example {processed}: {e}")
            print(traceback.format_exc())
            
        processed += 1
        pbar.set_postfix({"processed": processed, "saved": saved})
            
    pbar.close()
    print(f"Completed: {processed} processed, {saved} saved")


# python synthetic/query_writing.py --output_dir data/kddcup25_synthetic/query_writing