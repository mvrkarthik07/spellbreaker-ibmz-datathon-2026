"""Small local HTTP adapter around the prebuilt llama-cpp-python runtime."""
from __future__ import annotations

import json
import os
import platform
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from llama_cpp import Llama

MODEL_PATH = os.environ.get(
    "MODEL_PATH", "/models/granite-3.0-1b-a400m-instruct-be.Q4_K_M.gguf"
)
N_THREADS = int(os.environ.get("LLAMA_THREADS", "3"))
MODEL = Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=N_THREADS,
              n_batch=128, verbose=False)
MODEL_LOCK = threading.Lock()
ALLOWED_FIELDS = ("level", "risk", "scam_type", "reasons", "amount_band", "age_band")


class Handler(BaseHTTPRequestHandler):
    server_version = "SpellBreakerLocalLLM/1.0"

    def _write(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/health":
            self._write(404, {"error": "not found"})
            return
        self._write(200, {"status": "ok", "runtime": "llama-cpp-python",
                          "arch": platform.machine(), "model": os.path.basename(MODEL_PATH)})

    def do_POST(self) -> None:
        if self.path != "/generate":
            self._write(404, {"error": "not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 16_384:
                self._write(413, {"error": "request size out of range"})
                return
            source = json.loads(self.rfile.read(size))
            case = {key: source.get(key) for key in ALLOWED_FIELDS}
            reasons = case.get("reasons") or []
            if not isinstance(reasons, list) or len(reasons) > 8:
                self._write(400, {"error": "invalid reasons"})
                return
            scam_type = str(case.get("scam_type") or "unknown").replace("_", " ")
            user = f"Scam type: {scam_type}"
            messages = [
                {"role": "system", "content": (
                    "Return exactly one sentence in this format: 'The indicators support the "
                    "<scam type> review.' Replace <scam type> with the supplied scam type. "
                    "Do not add any other words or claims."
                )},
                {"role": "user", "content": user},
            ]
            with MODEL_LOCK:
                response = MODEL.create_chat_completion(
                    messages=messages, max_tokens=64, temperature=0.2,
                )
            note = response["choices"][0]["message"]["content"].strip()
            match = re.fullmatch(r"The indicators support the ([a-z ]+) review\.", note, re.IGNORECASE)
            if not match or match.group(1).strip().lower() != scam_type.lower():
                print(f"llama_http: rejected sentence text={note!r}", flush=True)
                raise ValueError("unverified model response")
            note = f"The indicators support the {scam_type} review."
            self._write(200, {"note": note, "runtime": "local-llm"})
        except Exception as exc:
            self._write(500, {"error": type(exc).__name__})

    def log_message(self, fmt: str, *args) -> None:
        print("llama_http: " + (fmt % args), flush=True)


if __name__ == "__main__":
    bind_host = os.environ.get("LLM_BIND_HOST", "127.0.0.1")
    server = ThreadingHTTPServer((bind_host, 8081), Handler)
    print(f"llama-cpp-python serving {MODEL_PATH} on {bind_host}:8081", flush=True)
    server.serve_forever()
