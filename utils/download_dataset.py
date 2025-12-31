import os
import json
import urllib.request
import zipfile

MBPP_URL = "https://raw.githubusercontent.com/google-research/google-research/master/mbpp/mbpp.jsonl"
HUMANEVAL_URL = "https://github.com/openai/human-eval/archive/refs/heads/master.zip"

DATA_DIR = "benchmarks"
MBPP_FILE = os.path.join(DATA_DIR, "mbpp.jsonl")
HUMANEVAL_DIR = os.path.join(DATA_DIR, "human-eval")


def download_mbpp():
    """Download MBPP dataset (JSONL) from Google Research repo."""
    print("[MBPP] Downloading...")
    os.makedirs(DATA_DIR, exist_ok=True)
    urllib.request.urlretrieve(MBPP_URL, MBPP_FILE)
    print(f"[MBPP] Saved to {MBPP_FILE}")

    # Optional: Preview first few questions
    with open(MBPP_FILE, "r") as f:
        for i, line in enumerate(f):
            if i == 3: break
            item = json.loads(line)
            print(f"  ▶ {item['text']} (id={item['task_id']})")


def download_humaneval():
    """Download and extract HumanEval benchmark."""
    print("[HumanEval] Downloading...")
    os.makedirs(DATA_DIR, exist_ok=True)

    zip_path = os.path.join(DATA_DIR, "human-eval.zip")
    urllib.request.urlretrieve(HUMANEVAL_URL, zip_path)
    print(f"[HumanEval] Downloaded zip to {zip_path}")

    # Extract only the data folder
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(DATA_DIR)

    # Move the human-eval/data folder to HUMAN_EVAL_DIR
    extracted_path = os.path.join(DATA_DIR, "human-eval-master")
    data_path = os.path.join(extracted_path, "data")

    if os.path.exists(data_path):
        os.rename(data_path, HUMANEVAL_DIR)

    # Cleanup
    os.remove(zip_path)
    print(f"[HumanEval] Extracted to {HUMANEVAL_DIR}")

    # Optional: Preview a single task
    sample_path = os.path.join(HUMANEVAL_DIR, "HumanEval_0.jsonl")
    if os.path.exists(sample_path):
        with open(sample_path, "r") as f:
            sample = json.loads(f.readline())
            print(f"  ▶ {sample['prompt']} (task_id={sample['task_id']})")


if __name__ == "__main__":
    print("🚀 Downloading benchmark datasets for code generation...")
    download_mbpp()
    download_humaneval()
    print("✅ All datasets are ready in the 'benchmarks' folder.")
