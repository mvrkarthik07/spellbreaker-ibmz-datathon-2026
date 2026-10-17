# LinuxONE evidence

- `platform.txt`: LinuxONE VM operating system, architecture, CPU count and memory.
- `cpu_features.txt`: exposed CPU feature flags and NNPA visibility.
- `container.txt`: container runtime, image, running service and configured user, or the documented venv fallback.
- `python_env.txt`: Python version and installed packages used by the service.
- `train_l1cc.log`: model training output, including the training architecture.
- `health.json`: live service architecture, trained-on architecture and runtime badge.
- `bench.txt`: 10,000-request localhost benchmark summary from LinuxONE.
- `crypto.txt`: OpenSSL version and SHA-256 speed output.
