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
ALLOWED_FIELDS = (
    "level", "risk_percent", "predicted_scam_type", "exact_reasons", "amount_band", "age_band"
)


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
            reasons = case.get("exact_reasons") or []
            if not isinstance(reasons, list) or len(reasons) > 8:
                self._write(400, {"error": "invalid reasons"})
                return
            if any(not isinstance(value, str) or len(value) > 240 for value in reasons):
                self._write(400, {"error": "invalid reason value"})
                return
            if any(len(str(case.get(key) or "")) > 120 for key in ("level", "risk_percent", "predicted_scam_type", "amount_band", "age_band")):
                self._write(400, {"error": "fact sheet value too long"})
                return
            facts = json.dumps(case, ensure_ascii=False, separators=(",", ":"))
            user = (
                "FACT SHEET (the only allowed facts):\n" + facts + "\n\n"
                "Return exactly four lines using this pattern and no other text:\n"
                "What happened: A <level> transfer in <amount_band> was flagged at <risk_percent> risk.\n"
                "Why suspicious: <exact reasons joined by semicolons>; age band: <age_band>.\n"
                "Likely scam: <predicted_scam_type>\n"
                "Next step: Independently verify the transfer using the bank's registered channel.\n"
                "Copy each fact exactly from the fact sheet. Do not add facts, types, names, account numbers, "
                "dates, amounts or any other numbers."
            )
            messages = [
                {"role": "system", "content": (
                    "You write a short fraud-analyst note. Use only the supplied fixed fact sheet. "
                    "Copy its values exactly; never infer, embellish, name an entity, or invent a number. "
                    "Output exactly four labeled lines and no markdown. The Likely scam value must exactly "
                    "equal predicted_scam_type. Limit the response to 120 tokens."
                )},
                {"role": "user", "content": (
                    "One formatting example (example facts are not facts about the current case):\n"
                    'FACT SHEET: {"level":"HIGH","risk_percent":"91.3%","predicted_scam_type":"investment",'
                    '"exact_reasons":["escalating payments","new recipient"],"amount_band":"S$1k–10k","age_band":"35-49"}\n'
                    "What happened: A HIGH transfer in S$1k–10k was flagged at 91.3% risk.\n"
                    "Why suspicious: escalating payments; new recipient; age band: 35-49.\n"
                    "Likely scam: investment\n"
                    "Next step: Independently verify the transfer using the bank's registered channel."
                )},
                {"role": "assistant", "content": (
                    "What happened: A HIGH transfer in S$1k–10k was flagged at 91.3% risk.\n"
                    "Why suspicious: escalating payments; new recipient; age band: 35-49.\n"
                    "Likely scam: investment\n"
                    "Next step: Independently verify the transfer using the bank's registered channel."
                )},
                {"role": "user", "content": user},
            ]
            with MODEL_LOCK:
                response = MODEL.create_chat_completion(
                    messages=messages, max_tokens=120, temperature=0, seed=42,
                )
            note = response["choices"][0]["message"]["content"].strip()
            self._write(200, {"note": note, "runtime": "llama-cpp-python"})
        except Exception as exc:
            self._write(500, {"error": type(exc).__name__})

    def log_message(self, fmt: str, *args) -> None:
        print("llama_http: " + (fmt % args), flush=True)


if __name__ == "__main__":
    bind_host = os.environ.get("LLM_BIND_HOST", "127.0.0.1")
    server = ThreadingHTTPServer((bind_host, 8081), Handler)
    print(f"llama-cpp-python serving {MODEL_PATH} on {bind_host}:8081", flush=True)
    server.serve_forever()
