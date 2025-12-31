from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen2.5-Coder-3B-Instruct",
    local_dir="./models/qwen_coder_3b",
    local_dir_use_symlinks=False
)
