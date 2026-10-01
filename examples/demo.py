#!/usr/bin/env python3
# claude-code-dashboard-term — a status line for Claude Code: model, usage limits, cost, context and git
# Copyright (C) 2026  lbecjx
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See LICENSE for the full text.
"""Print a sample Claude Code status-line payload, so you can try the script without a live session.

    python3 examples/demo.py | python3 statusline.py
    python3 examples/demo.py --critical | python3 statusline.py     # 5h window almost exhausted
    python3 examples/demo.py --opus --fast | python3 statusline.py
    python3 examples/demo.py --bedrock | python3 statusline.py      # no usage limits, long model id
    python3 examples/demo.py --spend | python3 statusline.py        # gateway spend limit

The payload follows the fields documented at https://code.claude.com/docs/en/statusline.
Reset times are relative to "now", so the demo always looks current.
"""
import json
import os
import sys
import time

now = time.time()
args = set(sys.argv[1:])

payload = {
    "session_name": "Sample session",
    "model": {"display_name": "Opus 5.5" if "--opus" in args else "Sonnet 5.5"},
    "workspace": {"current_dir": os.getcwd()},
    "effort": {"level": "high" if "--opus" in args else "medium"},
    "context_window": {
        "total_input_tokens": 612000 if "--critical" in args else 392000,
        "context_window_size": 1000000,
        "used_percentage": 61 if "--critical" in args else 39,
        "current_usage": {"input_tokens": 12400, "output_tokens": 1200,
                          "cache_read_input_tokens": 380000, "cache_creation_input_tokens": 5000},
    },
    "cost": {"total_cost_usd": 4.87},
    "rate_limits": {
        "five_hour": {"used_percentage": 92 if "--critical" in args else 34, "resets_at": now + 6300},
        "seven_day": {"used_percentage": 27, "resets_at": now + 6 * 86400 + 25200},
    },
}
if "--fast" in args:
    payload["fast_mode"] = True
if "--spend" in args:
    payload["rate_limits"] = {"spend_limit": {"used_percentage": 45, "resets_at": now + 3 * 86400}}
if "--bedrock" in args:
    payload["model"] = {"id": "us.anthropic.claude-sonnet-5-5-20260101-v1:0"}
    del payload["rate_limits"]

json.dump(payload, sys.stdout)
