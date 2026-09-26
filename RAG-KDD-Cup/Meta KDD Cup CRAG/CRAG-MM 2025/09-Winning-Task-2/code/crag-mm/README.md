#  Meta CRAG-MM Challenge 2025

This repo contains the first-place solution from `Team_NVIDIA` for the [Meta CRAG-MM Challenge 2025](https://www.aicrowd.com/challenges/meta-crag-mm-challenge-2025) - `Task 2: Multi-source Augmentation`. 

### Team Members
`Team_NVIDIA` consists of the following members:
- Chris Deotte (cdeotte@nvidia.com)
- Gilberto Titericz Jr (gtitericz@nvidia.com)
- Kazuki Onodera (konodera@nvidia.com)
- Ahmet Erdem (aerdem@nvidia.com)
- Raja Biswas (rabiswas@nvidia.com)

The following sections provide information about dependencies, training procedures, and data generation methods.


# Setup
We used `8xA100` GPUs for compute. Please run the following commands to setup the environment using conda:

```bash
conda create -n kddcup25 python=3.10 ipykernel jupyter
conda activate kddcup25
pip install --progress-bar off --no-cache-dir -U pip==21.0.1
pip install --progress-bar off --no-cache-dir vllm==0.7.3
pip install -r requirements.txt
python -m ipykernel install --user --name kddcup25 --display-name "kddcup25"
```

Please make sure to export required API keys:

```bash
export OPENAI_API_KEY=sk-proj-*** # for llm-as-a-judge
export NVDEV_ENDPOINT_KEY=*** # for query generation with llama 4 (optional - required only if you want to generate additional data)
```

# Artifacts

## Models
- The finetuned `meta-llama/Llama-3.2-11B-Vision-Instruct` model for our pipeline is available at `rbiswasfc/aicrowd-kddcup-v9`.

## Datasets
- The multi-task finetuning dataset is available at [rbiswasfc/kddcup-sft-datamix](https://huggingface.co/datasets/rbiswasfc/kddcup-sft-datamix)
- The images from the competition dataset is available at [rbiswasfc/kddcup-sft-images](https://huggingface.co/datasets/rbiswasfc/kddcup-sft-images)

The datasets are derived from the public_test split of `crag-mm-2025/crag-mm-single-turn-public` and `crag-mm-2025/crag-mm-multi-turn-public`datasets (v0.1.2).

# Fine-tuning

Please launch the fine-tuning run by running:

```bash
accelerate launch --num_processes=8 train.py
```
Note: please log in to your wandb account by running `wandb login` from the terminal to track the run. Its takes 1.5hr on a 8xA100 GPU node to complete.


# Data Generation Steps

## Generate synthetic query writing examples
To generate synthetic query writing exampes using the `meta/llama-4-maverick-17b-128e-instruct` model, run:

```bash
python synthetic/query_writing.py --output_dir data/kddcup25_synthetic/query_writing
```
Please note that it uses [build.nvidia.com NIM APIs](https://build.nvidia.com/) to call the model endpoints.

## Run agent for data generation
Now, run a data generating agent to produce intermediate data that will be used for multi-task finetuning dataset creation.

```bash
python data_gen.py --output_dir data/kddcup25_datagen_outputs --start_batch 0 --end_batch 500 --batch_size 4
```

## Create fine-tuning dataset

Please refer to:
- `notebooks/01_create_dataset.ipynb` for details on the multi-task finetuning dataset creation
- `notebooks/02_dataset_eda.ipynb` for the dataset exploration used in fine-tuning.