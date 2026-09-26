import os
import shutil
import json
from dotenv import load_dotenv


def download_datasets_from_kaggle(dst_dir):
    """
    Download datasets from kaggle API
    (icaif-24-finance-rag-challenge)
    """
    print("Download of kaggle dataset initiating...")

    # Load environment variables for `Kaggle API`
    load_dotenv()

    # Download dataset from Kaggle
    kaggle_competition = "icaif-24-finance-rag-challenge"
    download_command = f"kaggle competitions download -c {kaggle_competition}"
    os.system(download_command)

    # Create temporary directory for extraction
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    # Unzip dataset
    zip_file = f"{kaggle_competition}.zip"
    os.system(f"unzip -q {zip_file} -d {temp_dir}")
    os.remove(zip_file)  # Remove zip file after extraction

    # Define subsets and file structure
    subsets = {
        "FinDER": (
            "finder_queries.jsonl/queries.jsonl",
            "finder_corpus.jsonl/corpus.jsonl",
            "FinDER_qrels.tsv",
        ),
        "FinQABench": (
            "finqabench_queries.jsonl/queries.jsonl",
            "finqabench_corpus.jsonl/corpus.jsonl",
            "FinQABench_qrels.tsv",
        ),
        "MultiHiertt": (
            "multiheirtt_queries.jsonl/queries.jsonl",
            "multiheirtt_corpus.jsonl/corpus.jsonl",
            "MultiHeirtt_qrels.tsv",
        ),
        "ConvFinQA": (
            "convfinqa_queries.jsonl/queries.jsonl",
            "convfinqa_corpus.jsonl/corpus.jsonl",
            "ConvFinQA_qrels.tsv",
        ),
        "TATQA": (
            "tatqa_queries.jsonl/queries.jsonl",
            "tatqa_corpus.jsonl/corpus.jsonl",
            "TATQA_qrels.tsv",
        ),
        "FinanceBench": (
            "financebench_queries.jsonl/queries.jsonl",
            "financebench_corpus.jsonl/corpus.jsonl",
            "FinanceBench_qrels.tsv",
        ),
        "FinQA": (
            "finqa_queries.jsonl/queries.jsonl",
            "finqa_corpus.jsonl/corpus.jsonl",
            "FinQA_qrels.tsv",
        ),
    }

    # Create destination directory
    os.makedirs(dst_dir, exist_ok=True)

    # Move files to appropriate subset directories
    for subset, (query_file, corpus_file, qrel_file) in subsets.items():
        subset_dir = os.path.join(dst_dir, subset)
        os.makedirs(subset_dir, exist_ok=True)

        for src_file, dest_file in zip(
            (query_file, corpus_file, qrel_file),
            ("queries.jsonl", "corpus.jsonl", "qrels.tsv"),
        ):
            src_path = os.path.join(temp_dir, src_file)
            dest_path = os.path.join(subset_dir, dest_file)

            if os.path.exists(src_path):
                shutil.move(src_path, dest_path)
            else:
                raise FileNotFoundError(
                    f"Error: Dataset file ({src_file}) not found in {temp_dir}."
                )

    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    print("Download of kaggle dataset completed.")


def prepare_datasets(dataset_dir):
    """
    Merge corpus and queries into pair 
    """

    print("Dataset pre-processing initiating...")
    
    subsets = [
        "FinanceBench",
        "FinDER",
        "FinQABench",
        "MultiHiertt",
        "ConvFinQA",
        "TATQA",
        "FinQA",
    ]

    for subset in subsets:
        query_path = os.path.join(dataset_dir, subset, "queries.jsonl")
        with open(query_path, "r", encoding="utf-8") as f:
            query_id_list = [json.loads(line)["_id"] for line in f]

        corpus_path = os.path.join(dataset_dir, subset, "corpus.jsonl")
        with open(corpus_path, "r", encoding="utf-8") as f:
            corpus_id_list = [json.loads(line)["_id"] for line in f]

        prep_datasets = {}
        for query_id in query_id_list:
            prep_datasets[query_id] = {corpus_id: 0 for corpus_id in corpus_id_list}

        save_path = os.path.join(dataset_dir, subset, "merge.json")
        with open(save_path, "w") as f:
            json.dump(prep_datasets, f)

    print("Dataset pre-processing completed.")



if __name__ == "__main__":

    dataset_dir = "./dataset"
    download_datasets_from_kaggle(dataset_dir)
    prepare_datasets(dataset_dir)