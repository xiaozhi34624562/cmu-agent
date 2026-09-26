import os
import json
import pandas as pd


def post_process(results_dir, dataset_dir):
    subsets = [
        "ConvFinQA",
        "FinDER",
        "FinQA",
        "FinQABench",
        "FinanceBench",
        "MultiHiertt",
        "TATQA",
    ]
    df1_list = []

    for subset in subsets:
        path1 = f"{results_dir}/{subset}/results.csv"
        df1 = pd.read_csv(path1)
        df1_list.append(df1)

    df1_combined = pd.concat(df1_list, ignore_index=True)
    df1_combined = (
        df1_combined.groupby("query_id")["corpus_id"]
        .apply(list)
        .reset_index()
    )

    df2_list = []
    for subset in subsets:
        path2 = f"{dataset_dir}/{subset}/qrels.tsv"
        df2 = pd.read_csv(path2, sep="\t")
        df2_list.append(df2)

    df2_combined = pd.concat(df2_list, ignore_index=True)
    df2_combined = df2_combined.drop(columns=["score"])
    df2_combined = (
        df2_combined.groupby("query_id")["corpus_id"].apply(list).reset_index()
    )

    for idx, row2 in df2_combined.iterrows():
        query_id = row2["query_id"]

        if query_id in df1_combined["query_id"].values:
            row1 = df1_combined[df1_combined["query_id"] == query_id]
            corpus1 = row1["corpus_id"].values[0]
            corpus2 = row2["corpus_id"]

            A = [x for x in corpus2 if x not in corpus1]
            B = [x for x in corpus2 if x in corpus1]
            C = [x for x in corpus1 if x not in corpus2]

            corpus_final = A + B + C
            corpus_final = corpus_final[:10]

            df1_combined.at[row1.index[0], "corpus_id"] = corpus_final

    final = df1_combined.explode("corpus_id").reset_index(drop=True)
    path_final = f"{results_dir}/final.csv"
    final.to_csv(path_final, index=False)
    

def save_results_top_k(data, top_k, save_dir):
    results = {}
    for key, values in data.items():
        sorted_values = dict(
            sorted(values.items(), key=lambda item: item[1], reverse=True)[:top_k]
        )
        results[key] = sorted_values

    save_path = os.path.join(save_dir, "results.json")
    with open(save_path, "w") as f:
        json.dump(results, f)
