#!/usr/bin/env python3
import argparse
import json
from urllib import request

def post(url, data):
    req = request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    return request.urlopen(req).read().decode()

def get(url):
    return request.urlopen(url).read().decode()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True)
    parser.add_argument("cmd", choices=["put", "get", "status"])
    parser.add_argument("key", nargs="?")
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()

    base = args.node.rstrip("/")

    if args.cmd == "put":
        print(post(base + "/put", {"key": args.key, "value": args.value}))
    elif args.cmd == "get":
        print(get(base + f"/get?key={args.key}"))
    else:
        print(get(base + "/status"))

if __name__ == "__main__":
    main()
