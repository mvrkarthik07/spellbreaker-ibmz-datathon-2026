# LinuxONE evidence

- `platform.txt`: LinuxONE OS, architecture, CPU count and memory.
- `cpu_features.txt`: CPU flags and literal `grep -c nnpa /proc/cpuinfo` result.
- `container.txt`: Docker service, configured user, read-only root, tmpfs and dropped capabilities.
- `python_env.txt`: apt-backed project training environment and Ubuntu service container package versions.
- `train_l1cc.log`: SpellBreaker training output and MuleNet score source.
- `mulenet_l1cc.log`: official Jupyter image MuleNet command and XGBoost/HistGradientBoosting report.
- `genai_runtime.txt`: GenAI runtime status and Granite attempt outcome.
- `health.json`: live service architecture, trained-on architecture and runtime badge.
- `bench.txt`: 10,000-request localhost LinuxONE benchmark.
- `crypto.txt`: OpenSSL SHA-256 speed, MSA visibility and synthetic Python HMAC token sample.
- `genai_prompt_sample.txt`: synthetic, personal-data-free model prompt example.
- `SpellBreaker_on_LinuxONE.executed.ipynb`: executed service demo and notebook-only PyTorch MLP comparison against HistGradientBoosting.
