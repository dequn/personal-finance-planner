#!/usr/bin/env python3
"""CLI fallback for the Plugin's deterministic home-opportunity calculator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
MCP_ROOT = PLUGIN_ROOT / "mcp"
sys.path.insert(0, str(MCP_ROOT))

from personal_finance_planner.home import calculate_home_opportunity  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="JSON input file, or - for stdin",
    )
    args = parser.parse_args()

    if args.input == "-":
        payload = json.load(sys.stdin)
    else:
        with Path(args.input).open(encoding="utf-8") as handle:
            payload = json.load(handle)
    print(
        json.dumps(
            calculate_home_opportunity(**payload),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
