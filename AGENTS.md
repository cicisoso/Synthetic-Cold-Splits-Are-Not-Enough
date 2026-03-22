## 本机服务器

- SSH：无需登录远程SSH，直接在本机运行
- GPU：1x RTX 4090 24GB
- Conda 环境：`research`（Python 3.10 + PyTorch）
- 激活：`eval "$(/root/miniconda3/bin/conda shell.bash hook)" && conda activate research`
- 代码目录：`/root/exp/dti_codex`
- 后台运行用 `tmux`：`tmu new -s exp0 bash -c '...'`
