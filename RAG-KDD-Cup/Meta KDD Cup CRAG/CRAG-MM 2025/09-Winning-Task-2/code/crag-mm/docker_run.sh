#!/bin/bash

# Function to check if nvidia-container-toolkit is installed
check_nvidia_toolkit() {
    if ! command -v nvidia-container-toolkit &> /dev/null; then
        echo "WARNING: nvidia-container-toolkit is not installed!"
        echo "This script requires nvidia-container-toolkit for GPU access in Docker containers."
        echo "Please install it following the instructions at:"
        echo "https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        echo "Continuing without GPU support..."
        return 1
    fi
    return 0
}

# Check for HF_TOKEN environment variable
if [ -z "$HF_TOKEN" ]; then
    echo "======================================================"
    echo "WARNING: HF_TOKEN environment variable is not set!"
    echo "This may cause issues with Hugging Face model downloads."
    echo "Please set your Hugging Face token using:"
    echo "export HF_TOKEN=your_token_here"
    echo "======================================================"
    HF_TOKEN_FLAG="-e HF_TOKEN=None"
else
    HF_TOKEN_FLAG="-e HF_TOKEN=$HF_TOKEN"
fi

# Check for nvidia-container-toolkit
check_nvidia_toolkit
HAS_GPU_SUPPORT=$?

# This script builds a Docker image from the current directory and runs containers
# to execute task-specific evaluation scripts. The current directory is mounted
# at /submission inside the container for access to all necessary files.

# Parse command line arguments
TASK1=false
TASK2=false
TASK3=false

# Show usage instructions if no arguments are provided
if [ $# -eq 0 ]; then
    echo "Error: No task specified"
    echo "Usage: $0 [--task1] [--task2] [--task3]"
    echo "  --task1    Run only Task 1"
    echo "  --task2    Run only Task 2"
    echo "  --task3    Run only Task 3"
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --task1)
            TASK1=true
            shift
            ;;
        --task2)
            TASK2=true
            shift
            ;;
        --task3)
            TASK3=true
            shift
            ;;
        *)
            echo "Error: Unknown option: $1"
            echo "Usage: $0 [--task1] [--task2] [--task3]"
            echo "  --task1    Run only Task 1"
            echo "  --task2    Run only Task 2"
            echo "  --task3    Run only Task 3"
            exit 1
            ;;
    esac
done

# Step 1: Define the Docker image name using the current git commit hash
LAST_COMMIT_HASH=$(git rev-parse --short HEAD)
IMAGE_NAME="aicrowd/meta-comprehensive-rag-benchmark-starter-kit:${LAST_COMMIT_HASH}"

# Step 2: Build the Docker image
START_TIME=$(date +%s)
DOCKER_BUILDKIT=1 docker build -t $IMAGE_NAME .
BUILD_STATUS=$?
if [ $BUILD_STATUS -ne 0 ]; then
    echo "Docker build failed. Exiting..."
    exit $BUILD_STATUS
fi
END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))
echo "Total build time: $BUILD_TIME seconds"

# Get HF cache directory from environment variables, defaulting to standard location if not set
HF_CACHE_DIR=${HF_HOME:-${XDG_CACHE_HOME:-$HOME/.cache}}/huggingface
mkdir -p "$HF_CACHE_DIR"

# Step 3: Run the Docker container(s) based on selected tasks
# The container configuration:
# - Mounts the current directory to /submission for file access
# - Mounts the HF cache directory to avoid redownloading models
# - Sets the working directory to /submission
# - Enables GPU access with --gpus all (if available)
# - Uses host IPC namespace for better performance
if [ "$TASK1" = true ]; then
    echo "Running Task 1..."
    GPU_FLAG=""
    if [ $HAS_GPU_SUPPORT -eq 0 ]; then
        GPU_FLAG="--gpus all"
    fi
    docker run \
        $GPU_FLAG \
        -v "$(pwd)":/submission \
        -v "$HF_CACHE_DIR":/root/.cache/huggingface \
        -e HF_HOME=/root/.cache/huggingface \
        -e HF_HUB_ENABLE_HF_TRANSFER=1 \
        $HF_TOKEN_FLAG \
        -w /submission \
        --ipc=host \
        $IMAGE_NAME python local_evaluation.py --dataset-type single-turn --suppress-web-search-api
fi

if [ "$TASK2" = true ]; then
    echo "Running Task 2..."
    GPU_FLAG=""
    if [ $HAS_GPU_SUPPORT -eq 0 ]; then
        GPU_FLAG="--gpus all"
    fi
    docker run \
        $GPU_FLAG \
        -v "$(pwd)":/submission \
        -v "$HF_CACHE_DIR":/root/.cache/huggingface \
        -e HF_HOME=/root/.cache/huggingface \
        -e HF_HUB_ENABLE_HF_TRANSFER=1 \
        $HF_TOKEN_FLAG \
        -w /submission \
        --ipc=host \
        $IMAGE_NAME python local_evaluation.py --dataset-type single-turn 
fi

if [ "$TASK3" = true ]; then
    echo "Running Task 3..."
    GPU_FLAG=""
    if [ $HAS_GPU_SUPPORT -eq 0 ]; then
        GPU_FLAG="--gpus all"
    fi
    docker run \
        $GPU_FLAG \
        -v "$(pwd)":/submission \
        -v "$HF_CACHE_DIR":/root/.cache/huggingface \
        -e HF_HOME=/root/.cache/huggingface \
        -e HF_HUB_ENABLE_HF_TRANSFER=1 \
        $HF_TOKEN_FLAG \
        -w /submission \
        --ipc=host \
        $IMAGE_NAME python local_evaluation.py --dataset-type multi-turn 
fi
# Note: This script requires nvidia-container-toolkit to be installed and configured
# for GPU access. The script will run without GPU support if nvidia-container-toolkit
# is not available, but performance may be significantly impacted.

# Note: The Dockerfile should include all necessary dependencies and runtime
# configuration for running the evaluation scripts.

# Note: The .dockerignore file in the root directory should exclude unnecessary
# files (like large datasets or models) to optimize the build process.