import argparse
import concurrent.futures
import os
import time

import pandas as pd
from cragmm_search.search import UnifiedSearchPipeline
from datasets import Dataset, load_dataset
from openai import OpenAI
from pydantic import BaseModel
from tqdm.auto import tqdm

from agents.data_gen_agent import CragAgentDataGen
from crag_batch_iterator import CRAGTurnBatchIterator


def create_hf_dataset(data):    
    hf_dataset = Dataset.from_dict({k: [d[k] for d in data] for k in data[0].keys()})
    return hf_dataset

class CRAGTurnEvaluationResult(BaseModel):
    """Structured output model for CRAG turn evaluation results."""
    accuracy: bool
        
def get_system_message() -> str:
    """
    Returns the system message for the evaluator.
    """
    return (
        "You are an expert evaluator for question answering systems. "
        "Your task is to determine if a prediction correctly answers a question based on the ground truth.\n\n"
        "Rules:\n"
        "1. The prediction is correct if it captures all the key information from the ground truth.\n"
        "2. The prediction is correct even if phrased differently as long as the meaning is the same.\n"
        "3. The prediction is incorrect if it contains incorrect information or is missing essential details.\n"
        "Output a JSON object with a single field 'accuracy' whose value is true or false."
    )

def attempt_api_call(client, model_name, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            completion = client.beta.chat.completions.parse(model=model_name, messages=messages, response_format=CRAGTurnEvaluationResult)
            return completion.choices[0].message.parsed
        except Exception as e:
            time.sleep(0.2)
            error_message = f"API call failed on attempt {attempt + 1}/{max_retries}: {str(e)}"
            if attempt == max_retries - 1:
                print(f"[red]Failed after {max_retries} attempts: {str(e)}[/red]")
            else:
                print(f"[yellow]{error_message}, retrying...[/yellow]")
    return None

def evaluate_response(query, ground_truth, agent_response, eval_model_name = "gpt-4o-mini"):
    is_idk = "i don't know" in agent_response.lower()
    is_exact_match = agent_response.strip().lower() == ground_truth.strip().lower()
    is_semantically_correct = False
    api_response = None

    is_correct = is_exact_match

    if not is_idk and not is_exact_match:
        # local_openai_client = AzureOpenAI(api_version="2025-03-01-preview", azure_endpoint="https://llm-proxy.perflab.nvidia.com", api_key=os.environ["NV_PERFLAB_KEY"])
        local_openai_client = OpenAI()

        messages = [
            {"role": "system", "content": get_system_message()},
            {"role": "user", "content": f"Question: {query}\nGround truth: {ground_truth}\nPrediction: {agent_response}\n"},
        ]
        
        api_response = attempt_api_call(local_openai_client, eval_model_name, messages)
        
        if api_response:
            is_semantically_correct = api_response.accuracy
            is_correct = is_semantically_correct
    if is_exact_match:
        is_semantically_correct = True

    return {
        "is_exact_match": is_exact_match,
        "is_correct": is_correct,
        "is_miss": is_idk,
        "is_semantically_correct": is_semantically_correct,
        "api_response": api_response.model_dump()['accuracy'] if api_response else None,
    }

def evaluate_response_parallel(responses, max_workers=8):
    """
    Evaluate responses in parallel using ThreadPoolExecutor.
    
    Args:
        responses: List of response dictionaries
        max_workers: Number of parallel threads to use
    """
    
    def evaluate_single_response(response):
        query = response['query']
        ground_truth = response['answer']
        agent_response = response['predicted_answer']
        

        evaluation_result = evaluate_response(query, ground_truth, agent_response)

        response['eval_is_correct'] = evaluation_result['is_correct']
        response['eval_is_semantically_correct'] = evaluation_result['is_semantically_correct']
        response['eval_is_miss'] = evaluation_result['is_miss']
        response["eval_api_response"] = evaluation_result['api_response']
        
        return response
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_response = {
            executor.submit(evaluate_single_response, response): i 
            for i, response in enumerate(responses)
        }
        
        with tqdm(total=len(responses), desc="Evaluating responses") as pbar:
            for future in concurrent.futures.as_completed(future_to_response):
                try:
                    result = future.result()
                    pbar.update(1)
                except Exception as exc:
                    idx = future_to_response[future]
                    print(f'Response {idx} generated an exception: {exc}')
                    pbar.update(1)


def get_agent_inputs(batch, agent_response_map):
    interaction_ids = batch["interaction_ids"]
    queries = batch["queries"]
    images = batch["images"]
    conversation_histories = batch["conversation_histories"]

    message_histories = []
    interaction_id_histories = []

    for conversation_history in conversation_histories:
        message_history = []
        interaction_id_history = []

        for turn in conversation_history:
            turn_interaction_id = turn["interaction_id"]
            turn_agent_response = agent_response_map.get(turn_interaction_id)
            if not turn_agent_response:
                raise AssertionError(f"Agent response not found for turn {turn_interaction_id}. Did you shuffle the multi-turn conversations by mistake?")
            message_history.append({"role": "user", "content": turn["query"]})
            message_history.append({"role": "assistant", "content": turn_agent_response})
            interaction_id_history.append(turn_interaction_id)
        message_histories.append(message_history)
        interaction_id_histories.append(interaction_id_history)
    return {"queries": queries, "images": images, "message_histories": message_histories, "interaction_id_histories": interaction_id_histories}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=str, default="data/kddcup25_datagen_outputs")
    parser.add_argument("--start_batch", type=int, default=0)
    parser.add_argument("--end_batch", type=int, default=500)
    parser.add_argument("--batch_size", type=int, default=4)
    args = parser.parse_args()

    search_api_text_model_name = "BAAI/bge-large-en-v1.5"
    search_api_image_model_name = "openai/clip-vit-large-patch14-336"
    search_api_web_hf_dataset_id = "crag-mm-2025/web-search-index-public-test"
    search_api_image_hf_dataset_id = "crag-mm-2025/image-search-index-public-test"
    
    dataset_type = "single-turn"
    dataset_split = "public_test"
    repo_name = f"crag-mm-2025/crag-mm-{dataset_type}-public"

    output_dir = args.output_dir
    start_batch = args.start_batch
    end_batch = args.end_batch
    batch_size = args.batch_size

    search_pipeline = UnifiedSearchPipeline(
        text_model_name=search_api_text_model_name,
        image_model_name=search_api_image_model_name,
        web_hf_dataset_id=search_api_web_hf_dataset_id,
        image_hf_dataset_id=search_api_image_hf_dataset_id,
    )

    dataset = load_dataset(repo_name, revision="v0.1.2")[dataset_split]
    batch_iterator = iter(CRAGTurnBatchIterator(dataset=dataset, batch_size=batch_size, shuffle=False))

    agent = CragAgentDataGen(search_pipeline = search_pipeline)
    
    data = []
    pbar = tqdm(range(end_batch - start_batch))

    agent_response_map = {}
    start_time = time.time()
    for idx, batch in enumerate(batch_iterator):
        if idx < start_batch:
            continue
        print(f"Processing batch {idx-start_batch} of {end_batch - start_batch}")

        agent_inputs = get_agent_inputs(batch, agent_response_map)

        interaction_ids = batch["interaction_ids"]
        queries = batch["queries"]
        images = batch["images"]
        conversation_histories = batch["conversation_histories"]
        message_histories = agent_inputs["message_histories"]
        answers = batch['answers']
        
        responses = agent.batch_generate_response(queries, images, message_histories, answers)
        for response in responses:
            response['session_id'] = batch['session_ids'][response['example_idx']]
            response['interaction_id'] = batch['interaction_ids'][response['example_idx']]
            response['turn_idx'] = batch['turn_idxs'][response['example_idx']]
            response['dynamism'] = batch['dynamisms'][response['example_idx']]
            response['domain'] = batch['domains'][response['example_idx']]
            response['image_quality'] = batch['image_qualities'][response['example_idx']]
            response['query_category'] = batch['query_categories'][response['example_idx']]
            
        evaluate_response_parallel(responses, max_workers=32)
        data.extend(responses)

        # save data without image
        for response in responses:
            if 'image' in response:
                del response['image']
        
        # save responses as hf dataset
        save_dir = f"{output_dir}/batch_{idx}"
        os.makedirs(save_dir, exist_ok=True)
        ds_hf = Dataset.from_dict({k: [d[k] for d in responses] for k in responses[0].keys()})
        ds_hf.save_to_disk(save_dir)
        pbar.update(1)
        
        if idx >= end_batch:
            break
    pbar.close()

    # deleted image key from each element of data
    for item in data:
        if 'image' in item:
            del item['image']

    df = pd.DataFrame(data)
    print(df.groupby(['eval_is_correct'])['context_relevance'].mean().reset_index())

    ds_hf = create_hf_dataset(data)
    os.makedirs(output_dir, exist_ok=True)
    ds_hf.save_to_disk(output_dir)

    end_time = time.time()

    print(f"Time taken: {(end_time - start_time) / 60:.2f} minutes")
    num_examples = batch_size * (end_batch - start_batch)
    print(f"Time per example: {(end_time - start_time) / num_examples:.2f} seconds")


# python data_gen.py --output_dir data/kddcup25_datagen_outputs