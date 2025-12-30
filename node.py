#!/usr/bin/env python3
"""
Lab 2 — Lamport Clock + Replicated Key–Value Store (3 nodes)
Consistency: eventual (LWW with Lamport timestamp)
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request, parse
import argparse
import json
import threading
import time
from typing import Dict, Any, Tuple, List

lock = threading.Lock()

LAMPORT = 0
STORE: Dict[str, Tuple[Any, int, str]] = {}  # key -> (value, ts, origin)
NODE_ID = ""
PEERS: List[str] = []

# Scenario A: artificial delay (A -> C)
DELAY_RULES = {
    # filled dynamically in main()
}


# ---------------- Lamport clock ----------------

def lamport_tick_local() -> int:
    global LAMPORT
    with lock:
        LAMPORT += 1
        return LAMPORT


def lamport_on_receive(received_ts: int) -> int:
    global LAMPORT
    with lock:
        LAMPORT = max(LAMPORT, received_ts) + 1
        return LAMPORT


def get_lamport() -> int:
    with lock:
        return LAMPORT


# ---------------- Store logic ----------------

def apply_lww(key: str, value: Any, ts: int, origin: str) -> bool:
    with lock:
        cur = STORE.get(key)
        if cur is None:
            STORE[key] = (value, ts, origin)
            return True

        _, cur_ts, cur_origin = cur
        if ts > cur_ts or (ts == cur_ts and origin > cur_origin):
            STORE[key] = (value, ts, origin)
            return True

        return False


# ---------------- Replication ----------------

def replicate_to_peers(key: str, value: Any, ts: int, origin: str):
    payload = json.dumps({
        "key": key,
        "value": value,
        "ts": ts,
        "origin": origin
    }).encode()

    headers = {"Content-Type": "application/json"}

    for peer in PEERS:
        delay = DELAY_RULES.get((NODE_ID, peer), 0)
        if delay > 0:
            print(f"[{NODE_ID}] delaying send to {peer} by {delay}s")
            time.sleep(delay)

        try:
            req = request.Request(
                peer.rstrip("/") + "/replicate",
                data=payload,
                headers=headers,
                method="POST"
            )
            request.urlopen(req, timeout=2).read()
        except Exception as e:
            print(f"[{NODE_ID}] replicate failed to {peer}: {e}")


# ---------------- HTTP Handler ----------------

class Handler(BaseHTTPRequestHandler):

    def _send(self, code: int, obj: Dict[str, Any]):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/get"):
            qs = parse.urlparse(self.path).query
            key = parse.parse_qs(qs).get("key", [""])[0]

            with lock:
                cur = STORE.get(key)

            if cur is None:
                self._send(404, {"ok": False, "key": key})
            else:
                value, ts, origin = cur
                self._send(200, {
                    "ok": True,
                    "key": key,
                    "value": value,
                    "ts": ts,
                    "origin": origin,
                    "lamport": get_lamport()
                })
            return

        if self.path == "/status":
            with lock:
                snapshot = {
                    k: {"value": v, "ts": ts, "origin": o}
                    for k, (v, ts, o) in STORE.items()
                }

            self._send(200, {
                "ok": True,
                "node": NODE_ID,
                "lamport": get_lamport(),
                "peers": PEERS,
                "store": snapshot
            })
            return

        self._send(404, {"ok": False})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode())

        if self.path == "/put":
            key = body["key"]
            value = body["value"]

            ts = lamport_tick_local()
            applied = apply_lww(key, value, ts, NODE_ID)

            print(f"[{NODE_ID}] PUT {key}={value} ts={ts}")

            threading.Thread(
                target=replicate_to_peers,
                args=(key, value, ts, NODE_ID),
                daemon=True
            ).start()

            self._send(200, {
                "ok": True,
                "node": NODE_ID,
                "key": key,
                "value": value,
                "ts": ts,
                "lamport": get_lamport()
            })
            return

        if self.path == "/replicate":
            key = body["key"]
            value = body["value"]
            ts = body["ts"]
            origin = body["origin"]

            lamport_on_receive(ts)
            applied = apply_lww(key, value, ts, origin)

            print(f"[{NODE_ID}] RECV {key}={value} ts={ts} from {origin}")

            self._send(200, {"ok": True})
            return

        self._send(404, {"ok": False})

    def log_message(self, *_):
        pass


# ---------------- Main ----------------

def main():
    global NODE_ID, PEERS, DELAY_RULES

    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--peers", default="")
    args = parser.parse_args()

    NODE_ID = args.id
    PEERS = [p for p in args.peers.split(",") if p]

    # Scenario A: delay A → C
    if NODE_ID == "A":
        for p in PEERS:
            if p.endswith(":8002"):
                DELAY_RULES[(NODE_ID, p)] = 2.0

    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"[{NODE_ID}] listening on port {args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
