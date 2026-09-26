# FinanceRAG

Implementation of **[FinanceRAG](https://www.kaggle.com/competitions/icaif-24-finance-rag-challenge)**, a Finance specialized Retrieval-Augmented Generation (RAG) system for the **ACM-ICAIF '24 Competition**. Short paper was uploaded in **[Arxiv](https://arxiv.org/abs/2411.16732)**
- **Pre-Retrieval Phase**: Efficient query expansion and corpus refinement techniques to enhance the retrieval process. 
- **Multi-Stage Reranking**: Utilizes multiple reranker models to improve the quality of retrieved documents.
- **Long-Context Management**: Implements a novel approach for handling long context sizes during llm generation. (not included yet.)
<br/>

## 📋 Task 

- **Task 1**: Retrieve the top 10 most relevant corpora for a given query.
- ~~**Task 2**: Generate accurate answers using retrieved corpora, including handling large contexts and numerical data.~~
<br/>

## 📊 Datasets

Each dataset have queries and corpora.
- **FinDER**: Jargon and abbreviation handling in 10-K reports.  
- **FinQABench**: Detecting hallucinations, ensuring factuality in 10-K reports.  
- **FinanceBench**: Real-world financial queries from 10-K reports.  
- **TATQA**: Numerical reasoning with mixed text and tables.  
- **FinQA**: Multi-step reasoning with earnings reports (text + tables).  
- **ConvFinQA**: Conversational queries on earnings reports.  
- **MultiHiertt**: Complex reasoning across hierarchical tables in annual reports.
<br/>

## 📂 Repository Structure

```bash
FinanceRAG/
├── financerag/                   # Main module directory
│   ├── common/                   # Common utility functions
│   ├── generate/                 # Code for response generation
│   ├── rerank/                   # Code for reranking retrieved documents
│   └── retrieval/                # Code for document retrieval
├── dataset/                      # Dataset storage folder
├── paper/                        # Paper folder
├── pre_retrieval.py              # Script for pre-Retrieval
├── prepare_dataset.py            # Script for dataset download and preparation 
├── prompt.json                   # Configuration for pre-retrieval prompts
├── requirements.txt              # Python dependencies
├── rerank.py                     # Script for reranking
└── run.sh                        # Script for running the full pipeline
```
<br/>

## 📚 Requirements
- Python 3.10+
- CUDA 12.2+
- OpenAI API key
- Kaggle API key & username
- For details on Python packages, see `requirements.txt`.
<br/>

## 🚀 Getting Started
We recommend using **Google Colab Pro+ (A100)** for execution of this project, especially for python packages installation.

**1. Clone the repository**
```bash
git clone https://github.com/cv-lee/FinanceRAG.git
cd FinanceRAG
```

**2. Create a `.env` file**
```bash
touch .env
```

**3. Write the `.env` file as shown below**
```bash
# .env
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
KAGGLE_USERNAME=YOUR_KAGGLE_USERNAME
KAGGLE_KEY=YOUR_KAGGLE_KEY
```

**4. Execute the full pipeline**
- The `run.sh` script runs the full pipeline, including package installation and retrieval (task 1). 
- The final output for task 1 is saved to `results/final.csv`
```bash
bash run.sh
```
<br/>

## 🛠️ Trouble Shooting

**1. Flash Attention Installation Issues**
- Uncomment `pip uninstall -y transformer-engine` in the `run.sh` script.
- If the issue persists, refer to the official [Flash Attention GitHub repository](https://github.com/Dao-AILab/flash-attention).

**2. Retrieval Speed is slow**
- You can adjust the batch size using the `--batch_size` argument in `run.sh`.

<br/>

## 📝 Paper

Discover more in the full paper: [`Arxiv`](https://arxiv.org/abs/2411.16732)

### Abstract
> As Large Language Models (LLMs) increasingly address domainspecific problems, their application in the financial sector has expanded rapidly. Tasks that are both highly valuable and time-consuming, such as analyzing financial statements, disclosures, and related documents, are now being effectively tackled using LLMs. This paper details the development of a high-performance, finance-specific Retrieval-Augmented Generation (RAG) system for the ACM-ICAIF ’24 FinanceRAG competition. We optimized performance through ablation studies on query expansion and corpus refinement during the pre-retrieval phase. To enhance retrieval accuracy, we employed multiple reranker models. Notably, we introduced an efficient method for managing long context sizes during the generation phase, significantly improving response quality without sacrificing performance. Our key contributions include: (1) preretrieval ablation analysis, (2) an enhanced retrieval algorithm, and (3) a novel approach for long-context management. This work demonstrates the potential of LLMs in effectively processing and analyzing complex financial data to generate accurate and valuable insights. The source code and further details are available at https://github.com/cv-lee/FinanceRAG.
<br/>

## 📬 Contact
For questions, please contact us:
- [Joohyun Lee](https://www.linkedin.com/in/cv-lee/)
- Minji Roh
