import os
import pdb
import json
import torch
import argparse
import pandas as pd
from sentence_transformers import CrossEncoder
from financerag.common import post_process, save_results_top_k
from financerag.rerank import CrossEncoderReranker
from financerag.tasks import (
    FinDER,
    FinQABench,
    ConvFinQA,
    FinanceBench,
    MultiHiertt,
    TATQA,
    FinQA,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Reranking with CrossEncoder")

    parser.add_argument(
        "--task",
        type=str,
        choices=[
            "FinDER",
            "FinQABench",
            "ConvFinQA",
            "FinanceBench",
            "MultiHiertt",
            "TATQA",
            "FinQA",
        ],
        help="Specify the task to be used.",
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=[
            "jinaai/jina-reranker-v2-base-multilingual",
            "Alibaba-NLP/gte-multilingual-reranker-base",
            "BAAI/bge-reranker-v2-m3",
        ],
        help="Model name for CrossEncoder",
    )
    parser.add_argument(
        "--top_k", type=int, default=200, help="Top-K results to rerank"
    )
    parser.add_argument(
        "--batch_size", type=int, default=8, help="Batch size for reranking"
    )
    parser.add_argument(
        "--dataset_dir", type=str, default="./dataset", help="Directory of dataset"
    )
    parser.add_argument(
        "--dataset_filename",
        type=str,
        default="merge.json",
        help="Filename of rerank input",
    )
    parser.add_argument(
        "--save_dir",
        type=str,
        default="./results/rerank",
        help="Directory to save reranked results",
    )
    parser.add_argument(
        "--save_top_k",
        type=int,
        default=None,
        help="Number of Top-k Results to save. If None, does not save",
    )
    parser.add_argument(
    "--do_post_process", action="store_true", help="Do post-processing"
    )
    return parser.parse_args()


def rerank():
    args = parse_args()
    if args.do_post_process:
        post_process(args.save_dir, args.dataset_dir)
        return None

    task_classes = {
        "FinDER": FinDER,
        "FinQABench": FinQABench,
        "ConvFinQA": ConvFinQA,
        "FinanceBench": FinanceBench,
        "MultiHiertt": MultiHiertt,
        "TATQA": TATQA,
        "FinQA": FinQA,
    }
    task = task_classes[args.task]()

    if args.model == "Alibaba-NLP/gte-multilingual-reranker-base":
        config_args = {"torch_dtype": torch.float16, "attn_implementation": "sdpa"}
    else:
        config_args = {"torch_dtype": torch.bfloat16, "attn_implementation": "eager"}


    model = CrossEncoderReranker(
        CrossEncoder(
            args.model,
            trust_remote_code=True,
            config_args=config_args,
        )
    )

    dataset_dir = os.path.join(args.dataset_dir, args.task)
    dataset_path = os.path.join(dataset_dir, args.dataset_filename)

    with open(dataset_path, "r") as f:
        dataset = json.load(f)
    try:
        print(f"Rerank ({args.task}) initiating...")
        results = task.rerank(
            reranker=model,
            results=dataset,
            top_k=args.top_k,
            batch_size=args.batch_size,
        )
        task.save_results(output_dir=args.save_dir)

        if args.save_top_k:
            save_subset_dir = os.path.join(args.save_dir, args.task)
            os.makedirs(save_subset_dir, exist_ok=True)
            save_results_top_k(results, args.save_top_k, save_subset_dir)
        print(f"Rerank ({args.task}) completed.")

    except (FileNotFoundError, ValueError) as e:
        print(f"Rerank ({args.task}) Error : {e}.")
    


if __name__ == "__main__":
    rerank()
