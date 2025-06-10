# PaddleOCR_web
哈气的作业

## 环境配置

- 步骤：
  1. **安装 Conda**：确保目标电脑已安装 Conda（如 Miniconda）。
  2. **创建环境**：执行 `conda env create -f paddle_web_env.yml`。
  3. 处理依赖冲突：
     - 若提示包冲突，尝试使用 `conda env update -f paddle_web_env.yml --prune` 强制更新。
     - 若 `paddlepaddle-gpu` 下载失败，检查 CUDA 版本是否与显卡驱动兼容，或手动从 [PaddlePaddle 官网](https://www.paddlepaddle.org.cn/install/quick) 获取对应版本的安装命令。
- 注意事项：
  - 若目标电脑没有 GPU 或使用集成显卡：需将 `paddlepaddle-gpu` 替换为 `paddlepaddle`（CPU 版本），并删除所有 CUDA 相关依赖（如 `cuda-cudart`、`cudnn` 等）。
  - 若 CUDA 版本不匹配（如目标电脑仅支持 CUDA 11.x）：需修改 `environment.yml` 中的 CUDA 版本（如 `cuda-version=11.8`），并更新 `paddlepaddle-gpu` 版本（如 `paddlepaddle-gpu=2.6.2` 对应 CUDA 11.8）。

