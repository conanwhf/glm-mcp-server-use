#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

ENV_CANDIDATES = ["Z_AI_API_KEY", "ZAI_API_KEY", "GLM_API_KEY", "ZHIPU_API_KEY"]


def _extract_from_claude_json() -> str | None:
    path = Path.home() / ".claude.json"
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    found: str | None = None

    def walk(node):
        nonlocal found
        if found:
            return
        if isinstance(node, dict):
            # common auth header form
            headers = node.get("headers")
            if isinstance(headers, dict):
                auth = headers.get("Authorization")
                if isinstance(auth, str) and auth.strip():
                    val = auth.strip()
                    found = val.split(" ", 1)[1].strip() if val.lower().startswith("bearer ") else val
                    return

            # local stdio env form
            env = node.get("env") or node.get("environment")
            if isinstance(env, dict):
                for k in ENV_CANDIDATES:
                    v = env.get(k)
                    if isinstance(v, str) and v.strip():
                        found = v.strip()
                        return

            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return found


def get_key() -> str | None:
    for key_name in ENV_CANDIDATES:
        value = os.getenv(key_name)
        if value:
            return value.strip()
    return _extract_from_claude_json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve Z.AI API key from env or ~/.claude.json")
    parser.add_argument("--masked", action="store_true", help="print masked value")
    args = parser.parse_args()

    key = get_key()
    if not key:
        return 1

    if args.masked:
        if len(key) <= 8:
            print("*" * len(key))
        else:
            print(f"{key[:4]}***{key[-4:]}")
    else:
        print(key)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
