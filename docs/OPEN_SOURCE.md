# Open-source and data credits

| Package / data | Use | Link | License / status |
|---|---|---|---|
| Python | Runtime | https://www.python.org/ | PSF License |
| FastAPI | API | https://github.com/fastapi/fastapi | MIT |
| Uvicorn | ASGI server | https://github.com/encode/uvicorn | BSD-3-Clause |
| NumPy | Simulation and features | https://github.com/numpy/numpy | BSD-3-Clause |
| pandas | Optional CSV ingest | https://github.com/pandas-dev/pandas | BSD-3-Clause |
| scikit-learn | Predictive models and metrics | https://github.com/scikit-learn/scikit-learn | BSD-3-Clause |
| joblib | Model serialization | https://github.com/joblib/joblib | BSD-3-Clause |
| threadpoolctl | Limit inference thread oversubscription | https://github.com/joblib/threadpoolctl | BSD-3-Clause |
| pytest | Acceptance checks | https://github.com/pytest-dev/pytest | MIT |
| IBM AMLworld HI-Small | Receiver-side transaction data used by MuleNet; 454 MB copy present in `data/HI-Small_Trans.csv` | https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml | CDLA-Sharing-1.0; comply with licence terms before redistribution |
| httpx2 | TestClient HTTP transport for acceptance checks | https://pypi.org/project/httpx2/ | MIT |
| Chart.js | Dashboard charts | https://www.chartjs.org/ | MIT |
| llama-cpp-python | Attempted local Granite inference; deterministic template retained after factuality validation | https://github.com/abetlen/llama-cpp-python | MIT |
| IBM Granite 3.0 1B A400M Instruct (Q4_K_M, big-endian GGUF) | Local analyst-note summary; only allowed case fields are sent to the local model process | https://huggingface.co/taronaeo/Granite-3.0-1B-A400M-Instruct-BE-GGUF | Apache-2.0 model family; quantized artifact hosted by taronaeo |
| LinuxONE Community Cloud Jupyter Lab ML image | Prebuilt s390x llama-cpp-python runtime and notebook execution | https://github.com/linuxone-community-cloud/jupyter-lab-ml | Image published for LinuxONE Community Cloud |

All application code in this repository was authored for this project. The synthetic victim-side records are generated locally and are not real transactions. Review each upstream license and the dataset terms before redistribution.
