#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    extensions_map = SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map.update({
        ".md": "text/plain; charset=utf-8",
        ".markdown": "text/plain; charset=utf-8",
    })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Serve a directory for Markdown Viewer"
            " with UTF-8 .md support."
        )
    )
    parser.add_argument(
        "root",
        help="配信対象のディレクトリパス",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="待ち受けホスト。デフォルト: 0.0.0.0",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="待ち受けポート。デフォルト: 8000",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root_path = Path(args.root).expanduser().resolve()

    if not root_path.exists():
        raise FileNotFoundError(f"指定されたパスが存在しません: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"指定されたパスはディレクトリではありません: {root_path}")

    os.chdir(root_path)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"serving: {root_path}")
    print(f"url: http://localhost:{args.port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
