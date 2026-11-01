import requests
import time
import re
import os
import hashlib
import json
import diskcache
from openai import OpenAI
from llm_config import cache_namespace, get_llm_config, get_llm_timeout

_CHOICE_TOKEN_RE = re.compile(r'^[A-Za-z\[\\\]\^_`]{1,2}$')
JUDGE_PROMPT_VERSION = "level-34-judge-v1"
_JUDGE_CACHE = diskcache.Cache(
    f"./{cache_namespace('level_34_judge_diskcache', JUDGE_PROMPT_VERSION)}"
)


def _looks_like_choice_token(s) -> bool:
    if not isinstance(s, str):
        return False
    return bool(_CHOICE_TOKEN_RE.fullmatch(s.strip()))


def _is_multi_choice_list(items) -> bool:
    if not items:
        return False
    return all(_looks_like_choice_token(x) for x in items)


def get_ai_response(question, max_retries=3, max_tokens=5000, temperature=0.):
    api_key, base_url, model = get_llm_config()
    
    if not api_key or not model:
        raise ValueError("OPENAI_API_KEY or OPENAI_API_MODEL environment variable not found")
    cache_key = hashlib.sha256(
        json.dumps(
            {
                "question": question,
                "model": model,
                "base_url": base_url,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "prompt_version": JUDGE_PROMPT_VERSION,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    cached = _JUDGE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    # 初始化OpenAI客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=get_llm_timeout(),
    )

    messages = [{"role": "user", "content": question}]

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                # 指数退避重试间隔
                time.sleep(2 ** (attempt - 1))
                
            # 调用官方SDK的聊天接口
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            
            # 提取回复内容
            content = response.choices[0].message.content
            if content:
                _JUDGE_CACHE.set(cache_key, content)
                return content
            
        except Exception as e:
            # 捕获其他未知异常
            print(f"Unexpected error: {str(e)}, retrying... (attempt {attempt})")

    return None
def extract_num_from_string(s: str) -> float:
    prompt = f"""
        Please extract the number from the string and put the number in \\boxed{{NUMBER}}. If the string contains multiple numbers, please extract the average of the numbers. If the string does not contain any number, please answer \\boxed{{None}}.
        STRING: {s}
        """
    ans = get_ai_response(prompt)
    match = re.search(r"\\boxed\{([^}]+)\}", ans)
    if match:
        num_str = match.group(1)
        if num_str.lower() == 'none':
            return None
        try:
            return float(num_str)
        except ValueError:
            # Translated from Chinese
            print(f"Could not convert extracted string to number: {num_str}")
            return None
    else:
        # Translated from Chinese
        print("Did not find a valid number format")
        return None

def judge_rank(original_question, extracted_prediction, real_answer):
    prompt_rank = f"""
        You're a judger to judge whether the model's prediction is completely aligned with the real answer. You will be given the original question, the model prediction, and the real answer. Please judge if the model prediction is completely correct. Only answer \\boxed{{Yes}} or \\boxed{{No}}.

        ORIGINAL_QUESTION: {original_question}

        MODEL_PREDICTION: {extracted_prediction}

        REAL_ANSWER: {real_answer}

        Two items "match" when they refer to the same entity in content, regardless of differences in wording, abbreviation, or language. Items do NOT need to be exact string matches.

        Decide using these rules:
        - Answer \\boxed{{Yes}} if MODEL_PREDICTION and REAL_ANSWER have the same length AND the i-th item of MODEL_PREDICTION matches the i-th item of REAL_ANSWER for every i.
        - Before outputting \\boxed{{Yes}}, you MUST explicitly write out the position-by-position comparison for every position.
        - Otherwise, answer \\boxed{{No}}.

        Important: for \\boxed{{Yes}}, positions must match item by item. Set-equivalence with reordered items is \\boxed{{No}}, NOT \\boxed{{Yes}}.
        Example:
        - MODEL_PREDICTION ["item2", "item1", "item3"] vs REAL_ANSWER ["item1", "item2", "item3"] -> \\boxed{{No}}

        Important: for \\boxed{{Yes}}, MODEL_PREDICTION and REAL_ANSWER must have the same length.
        Example:
        - MODEL_PREDICTION ["item1", "item2", "item3", "item4"] vs REAL_ANSWER ["item1", "item2", "item3"] -> \\boxed{{No}}
    """
    ans = get_ai_response(prompt_rank)
    return ans 

def judge_rank_detail(original_question, extracted_prediction, real_answer):
    prompt_rank = f"""
        You're a judger to judge whether the model's prediction aligns with the real answer. You will be given the original question, the model prediction, and the real answer. Please calculate how many items are overlapped. When comparing two items, only consider whether they are matched in content, ignore the difference in language. Answer that number with format: \\boxed{{NUMBER}}.

        ORIGINAL_QUESTION: {original_question}

        MODEL_PREDICTION: {extracted_prediction}

        REAL_ANSWER: {real_answer}
        
        Remember that for a ranking task, when the two have overlap, you have to calculate how many items are overlapped, and answer with that number \\boxed{{NUMBER}}, even if the order may be different.
    """
    ans = get_ai_response(prompt_rank)
    return ans 

def judge_str_match(extracted_prediction, real_answer):
    """
    Judges if the extracted prediction matches the real answer.
    :param extracted_prediction: The model's extracted prediction
    :param real_answer: The ground truth answer
    :return: Match result (1.0 for match, 0.0 for no match)
    """
    if isinstance(real_answer, int):
        extracted_prediction, real_answer = str(extracted_prediction), str(real_answer)
    prompt = f"""
        Please judge whether the model's prediction matches the real answer. Only compare the content, ignore the language. For example, "New York" and "NYC" are considered a match. Only answer \\boxed{{Yes}} or \\boxed{{No}}. 
        If they match, answer \\boxed{{Yes}}. 
        If they do not match, answer \\boxed{{No}}.

        MODEL_PREDICTION: {extracted_prediction}

        REAL_ANSWER: {real_answer}
    """
    ans = get_ai_response(prompt)
    if 'yes' in ans.lower():
        return 1.0
    else:
        return 0.0

def judge_rank_overall(original_question, model_prediction, real_answer):
    """
    original_question: The prediction question
    model_prediction: The model's output response
    real_answer: The answer from the JSON, which is a list
    """
    if _is_multi_choice_list(real_answer) and _is_multi_choice_list(model_prediction):
        real_answer = sorted(s.strip() for s in real_answer)
        model_prediction = sorted(s.strip() for s in model_prediction)
        if real_answer == model_prediction:
            return 1.0

    ans1 = judge_rank(original_question, model_prediction, real_answer)
    # print(original_question, model_prediction, real_answer, ans1)
    if 'yes' in ans1.lower():
        return 1.0 
    else:
        ans2 = judge_rank_detail(original_question, model_prediction, real_answer)
        match = re.search(r"\\boxed\{(\d+)\}", ans2)
        number = match.group(1)
        return (int(number)/float(len(real_answer)))*0.8


def judge_unordered_set_overall(original_question, model_prediction, real_answer):
    """Score a set of entities without imposing an order on the submission."""
    prediction = list(dict.fromkeys(str(item).strip() for item in model_prediction))
    answer = list(dict.fromkeys(str(item).strip() for item in real_answer))
    if not answer:
        return 1.0 if not prediction else 0.0

    if {item.casefold() for item in prediction} == {item.casefold() for item in answer}:
        return 1.0

    prompt = f"""
You are scoring an unordered set answer. Compare entities by meaning, allowing
aliases, abbreviations, and language differences. Order is irrelevant. Count
each entity at most once. Return only \\boxed{{N}}, where N is the number of
one-to-one semantic matches between the two sets.

QUESTION:
{original_question}

MODEL_SET:
{prediction}

GROUND_TRUTH_SET:
{answer}
"""
    # DeepSeek V4 Flash can use an internal reasoning trace before emitting
    # the boxed match count, so a small output budget can leave content empty.
    response = get_ai_response(prompt, max_tokens=512)
    match = re.search(r"\\boxed\{(\d+)\}", response or "")
    if not match:
        return 0.0
    matched = min(int(match.group(1)), len(answer), len(prediction))
    return 1.0 if matched == len(answer) == len(prediction) else matched / len(answer) * 0.8

def judge_number_overall(model_prediction, real_answer, std=1.0):
    return max(0, 1-((model_prediction-real_answer)/std)**2)

def judge_level_34_score(originaL_question, model_prediction, real_answer, std=1.0):
    if len(real_answer) == 1:
        if isinstance(real_answer[0], (float, int)) and not isinstance(real_answer[0], bool):
            if isinstance(model_prediction[0], (float, int)) and not isinstance(model_prediction[0], bool):
                return judge_number_overall(model_prediction[0], real_answer[0], std)
            else:
                extracted_prediction = extract_num_from_string(model_prediction[0])
                if extracted_prediction is None or std is None:
                    return 0.
                else:
                    return judge_number_overall(extracted_prediction, real_answer[0], std)
        else:
            return judge_str_match(model_prediction[0], real_answer[0])
    else:
        return judge_rank_overall(originaL_question, model_prediction, real_answer)

if __name__ == "__main__":
    # Translated example
    original_question = "In the daily short drama chart, what is the top-ranked drama? (Answer with the name only)",
            
    real_answer = ['The Phoenix Rises']
    model_prediction = ['My CEO Husband']
    result = judge_level_34_score(original_question, model_prediction, real_answer, std=None)
    print(result)