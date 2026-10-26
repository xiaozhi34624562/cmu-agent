from typing import List, Set, Dict, Any
from tenacity import retry, stop_after_attempt, wait_random_exponential
from concurrent.futures import ThreadPoolExecutor
import traceback
import concurrent.futures
import ast
import re
from llm_judge_level_34 import judge_level_34_score, judge_unordered_set_overall
from llm_config import get_llm_config, get_llm_timeout
from metric_router import MetricRoute, route_questions
from utils import to_float
import os
from openai import OpenAI


def extract_boxed_for_type_b(text):
    """Strip a surrounding ``\\boxed{...}`` / ``\\text{...}`` wrapper if present."""
    if not isinstance(text, str):
        return str(text)
    match = re.search(r"(?:oxed|ext)\{(.*?)\}", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _normalize_type_a_label(item):
    """Normalise one Type-A label so \\boxed{A}/\\text{A} compares equal to A."""
    text = str(item).strip().strip("\"'")
    match = re.fullmatch(r"\\(?:boxed|text)\{(.*)\}", text, flags=re.DOTALL)
    if match:
        text = match.group(1).strip().strip("\"'")
    if re.fullmatch(r"[A-Za-z]", text):
        return text.upper()
    if re.fullmatch(r"yes|no", text, flags=re.IGNORECASE):
        return "Yes" if text.lower() == "yes" else "No"
    return text


def _as_type_a_labels(value):
    """Coerce a raw Type-A ground-truth / prediction into a normalised label list."""
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                value = ast.literal_eval(text)
            except Exception:
                value = [text]
        else:
            value = [text]
    if isinstance(value, (set, list, tuple)):
        items = list(value)
    else:
        items = [value]
    return [_normalize_type_a_label(item) for item in items if str(item).strip() != ""]

def log_before_retry(retry_state):
    """Log before each retry"""
    print(
        f"Attempt {retry_state.attempt_number} failed, retrying in {retry_state.next_action.sleep} seconds..."
    )

def extract_by_gpt(questions: List[str], draft_answers: List[str]):
    api_key, base_url, model_name = get_llm_config()
    # Create a general OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=get_llm_timeout(),
    )
    
    prompt = "Given the question and a draft answer, please extract the answer from the draft answer. If the answer is wrapped in \\boxed{{}}, \\text{{}} or other format, please extract the content inside the braces. Finally, identify if the answer is a number. Please only output the extracted answer and whether the answer is an number, without outputing other any content. For example:\n$115\nyes\nAnother example:\nBeijing\nNo \n\nQeustion: {question}\n\nDraft Answer: {answer}"
    
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(4), before_sleep=log_before_retry)
    def process_single(question, draft_answer):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt.format(question=question, answer=draft_answer)}
                ],
                timeout=90,
            ).choices[0].message.content
            return response
        except Exception as e:
            print(f"An error occurred: {e}. Retrying...")
            raise  # Must re-raise the exception for tenacity to catch and retry
    
    # Use ThreadPoolExecutor to execute multithreaded tasks
    with ThreadPoolExecutor(max_workers=4) as executor:  # Number of threads can be adjusted
        responses = list(executor.map(process_single, questions, draft_answers))
    
    return responses

def extract_answer(title, event):
    if 'answer' in event and 'prediction' not in event:
        event['prediction'] = event['answer']
    if event['prediction'] is None:
        return None
    if isinstance(event['prediction'], list):
        event['prediction'] = event['prediction'][0]
    
    result = extract_by_gpt([title + '\n',], [event['prediction']])[0]
    event['prediction'] = '\n'.join(result.split('\n')[:-1])
    is_number = result.split('\n')[-1].strip()

    if is_number.lower() == 'yes':
        event['prediction'] = [to_float(event['prediction'])]
    else:
        if ',' in event['prediction']:
            event['prediction'] = [x.strip() for x in event['prediction'].split(',')]
        else:
            event['prediction'] = [event['prediction']] # unify the format
    
    return event['prediction']


def extract_answers(titles, events):
    """Batch version of ``extract_answer`` for a submission's full week."""
    if len(titles) != len(events):
        raise ValueError("titles and events must align")

    drafts = []
    for event in events:
        if "answer" in event and "prediction" not in event:
            event["prediction"] = event["answer"]
        prediction = event.get("prediction")
        if isinstance(prediction, list):
            prediction = prediction[0] if prediction else None
        drafts.append(prediction)

    valid_indices = [index for index, draft in enumerate(drafts) if draft is not None]
    extracted = [None] * len(events)
    if valid_indices:
        results = extract_by_gpt(
            [titles[index] + "\n" for index in valid_indices],
            [drafts[index] for index in valid_indices],
        )
        for index, result in zip(valid_indices, results):
            answer = "\n".join(result.split("\n")[:-1])
            is_number = result.split("\n")[-1].strip()
            if is_number.lower() == "yes":
                extracted[index] = [to_float(answer)]
            elif "," in answer:
                extracted[index] = [item.strip() for item in answer.split(",")]
            else:
                extracted[index] = [answer]
    return extracted

def estimate_score_level_1_2(
    questions: List[str],
    y_true_raw: List[Set[str]], 
    y_pred_raw: List[Set[str]]
) -> Dict[str, Any]:
    """
    Evaluates multi-label classification performance, safely handling empty inputs.
    """
    assert len(y_true_raw) == len(y_pred_raw), "The lengths of the true labels and predicted labels lists must be the same."
    
    f1_scores = []
    for y_true, y_pred in zip(y_true_raw, y_pred_raw):
        y_true = _as_type_a_labels(y_true)
        y_pred = _as_type_a_labels(y_pred)
        if len(y_true) == 1:
            f1_scores.append(1.0 if y_true == y_pred else 0.0)
            continue
        # Ensure data is of set type for easy intersection and difference calculations
        y_true = set(y_true)
        y_pred = set(y_pred)
        
        # --- Calculate F1-score for a single question ---
        
        # If both true and predicted are empty sets
        if not y_true and not y_pred:
            f1_scores.append(0.)
            continue
            
        # Calculate TP (True Positives): The correctly predicted part, i.e., the intersection
        tp = len(y_true.intersection(y_pred))
        
        # Calculate Precision (Precision = TP / |Predicted|)
        # |Predicted| = TP + FP (False Positives)
        if len(y_pred) == 0:
            precision = 0.0
        else:
            precision = tp / len(y_pred)
            
        # Calculate Recall (Recall = TP / |True|)
        # |True| = TP + FN (False Negatives)
        if len(y_true) == 0:
            recall = 0.0
        else:
            recall = tp / len(y_true)
            
        # Calculate F1-score (F1 = 2 * Precision * Recall / (Precision + Recall))
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
            
        f1_scores.append(f1)

    # --- Average the F1-scores for all questions ---
    if not f1_scores:
        return 0.0
    return f1_scores, sum(f1_scores) / len(f1_scores)


def estimate_type_a_score(
    y_true_raw: List[Set[str]],
    y_pred_raw: List[Set[str]],
) -> Dict[str, Any]:
    """
    Backward-compatible API aligned with the local evaluator.
    """
    return estimate_score_level_1_2([], y_true_raw, y_pred_raw)

def estimate_score_level_3_4(questions, y_true_raw, y_pred_raw, stds, max_workers=8):
    """
    Estimates the score for Type B questions using a thread pool and caching.
    """
    # 2. Add lru_cache decorator to the worker function
    # maxsize=None means the cache can grow indefinitely, you can also set a specific value, e.g., maxsize=1024
    def _normalize_gt(answer):
        if not isinstance(answer, list):
            answer = [answer]
        answer = [
            extract_boxed_for_type_b(item) if isinstance(item, str) else item
            for item in answer
        ]
        if len(answer) == 1:
            if isinstance(answer[0], str):
                try:
                    answer[0] = float(answer[0])
                except ValueError:
                    pass
            elif isinstance(answer[0], int) and not isinstance(answer[0], bool):
                answer[0] = float(answer[0])
        return answer

    def worker(question, y_true, y_pred, std):
        """
        A wrapper function to call the judging API. Results are now cached.
        """
        try:
            y_true = _normalize_gt(y_true)
            if type(y_true[0]) in [float, int]:
                if y_true[0] == 0:
                    std = 0.01
                else:
                    std = 0.05 * y_true[0]
            # judge_level_34_score will only be called the first time the (question, y_true, y_pred) combination appears
            return judge_level_34_score(
                originaL_question=question,
                model_prediction=y_pred,
                real_answer=y_true,
                std=std
            )
        except Exception as e:
            print(f"Error processing question at [estimate_type_b_score]: {question}, pred: {y_pred}, true: {y_true}. Error: {e}")
            traceback.print_exc()
            return 0.0
    
    if not all([questions, y_true_raw, y_pred_raw, stds]):
        return 0.0

    all_scores = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # The map function will map identical tasks (worker calls with the same parameters) to the cached results
       results = executor.map(worker, questions, y_true_raw, y_pred_raw, stds)
       all_scores = list(results)

    avg_score = sum(all_scores) / len(questions) if questions else 0.0
    
    return all_scores, avg_score


def estimate_type_b_score(questions, y_true_raw, y_pred_raw, stds, max_workers=8):
    """
    Backward-compatible API aligned with the local evaluator.
    """
    return estimate_score_level_3_4(questions, y_true_raw, y_pred_raw, stds, max_workers=max_workers)


def prewarm_metric_routes(
    questions,
    ground_truths,
    *,
    levels=None,
    question_ids=None,
):
    """Route every question once before scoring any model submissions.

    ``route_questions`` caches by question/GT/model, so subsequent model
    submissions reuse these results without another router API call.
    """
    return route_questions(
        questions,
        ground_truths,
        levels=levels,
        question_ids=question_ids,
    )


def estimate_routed_scores(
    questions,
    y_true_raw,
    y_pred_raw,
    stds,
    *,
    levels=None,
    question_ids=None,
):
    """Score predictions using one cached LLM metric route per question.

    Existing Type-A and Type-B functions remain unchanged.  Only routes marked
    ``unordered_set`` use the new scorer.
    """
    if not (len(questions) == len(y_true_raw) == len(y_pred_raw) == len(stds)):
        raise ValueError("questions, ground truths, predictions, and stds must align")

    routes = prewarm_metric_routes(
        questions,
        y_true_raw,
        levels=levels,
        question_ids=question_ids,
    )
    scores = [None] * len(questions)
    route_indices = {
        metric: [index for index, route in enumerate(routes) if route.metric == metric]
        for metric in ("legacy_type_a", "legacy_type_b", "unordered_set")
    }

    type_a_indices = route_indices["legacy_type_a"]
    if type_a_indices:
        type_a_scores, _ = estimate_type_a_score(
            [y_true_raw[index] for index in type_a_indices],
            [y_pred_raw[index] for index in type_a_indices],
        )
        for index, score in zip(type_a_indices, type_a_scores):
            scores[index] = score

    type_b_indices = route_indices["legacy_type_b"]
    if type_b_indices:
        type_b_scores, _ = estimate_type_b_score(
            [questions[index] for index in type_b_indices],
            [y_true_raw[index] for index in type_b_indices],
            [y_pred_raw[index] for index in type_b_indices],
            [stds[index] for index in type_b_indices],
        )
        for index, score in zip(type_b_indices, type_b_scores):
            scores[index] = score

    unordered_indices = route_indices["unordered_set"]
    if unordered_indices:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            unordered_scores = executor.map(
                lambda index: judge_unordered_set_overall(
                    questions[index], y_pred_raw[index], y_true_raw[index]
                ),
                unordered_indices,
            )
            for index, score in zip(unordered_indices, unordered_scores):
                scores[index] = score

    average = sum(scores) / len(scores) if scores else 0.0
    return scores, average, routes

if __name__ == "__main__":
    questions = [
        "What is the answer?",
        "What is the answer?",
    ]
    y_true_1_2 = [
        set(["A"]), 
        set(["A", "B"]),
    ]
    y_pred_1_2 = [
        set(["\\boxed{C}"]), 
        set(["\\boxed{D}", "\\boxed{B}"]), 
    ]
    y_pred_1_2 = [extract_answer(questions[i], {"prediction": pred}) for i, pred in enumerate(y_pred_1_2)]
    scores_1_2, avg_score_1_2 = estimate_score_level_1_2(questions, y_true_1_2, y_pred_1_2)
