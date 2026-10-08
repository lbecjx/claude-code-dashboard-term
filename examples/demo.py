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
    python3 examples/demo.py --speed | python3 statusline.py        # writes a sample transcript to a temp file
    python3 examples/demo.py --story | python3 statusline.py        # temp git repo with a workflow-dev story cost index

The payload follows the fields documented at https://code.claude.com/docs/en/statusline.
Reset times are relative to "now", so the demo always looks current.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

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

if "--speed" in args:
    # One prompt, a tool call written in two rows (same id), its result, and a final answer: 1400 output tokens over
    # 3.1 + 8 seconds of model time (the 2 seconds the tool ran are not counted), so the status line shows ~126 tok/s.
    start = datetime.now(timezone.utc) - timedelta(seconds=13)
    at = lambda seconds: (start + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    rows = [
        {"type": "user", "timestamp": at(0), "message": {"role": "user", "content": "Sample prompt"}},
        {"type": "assistant", "timestamp": at(3), "message": {"id": "msg_1", "role": "assistant", "usage": {"output_tokens": 400}}},
        {"type": "assistant", "timestamp": at(3.1), "message": {"id": "msg_1", "role": "assistant", "usage": {"output_tokens": 400}}},
        {"type": "user", "timestamp": at(5), "message": {"role": "user", "content": [{"type": "tool_result"}]}},
        {"type": "assistant", "timestamp": at(13), "message": {"id": "msg_2", "role": "assistant", "usage": {"output_tokens": 1000}}},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", prefix="statusline-demo-", delete=False) as f:
        f.write("\n".join(json.dumps(r) for r in rows) + "\n")
    payload["transcript_path"] = f.name

if "--story" in args:
    # A throwaway git repository holding the index workflow-dev writes after each story checkpoint, so line 1 shows
    # the story's cost (≥ because part of it is an estimate) next to the session's.
    repo = tempfile.mkdtemp(prefix="statusline-demo-")
    subprocess.run(["git", "init", "-q", repo], check=True)
    usage = os.path.join(repo, ".workflow-dev", "context", ".usage")
    os.makedirs(usage)
    with open(os.path.join(usage, ".index.json"), "w") as f:
        json.dump({"schema": "workflow-dev.usage/1", "last_story": "PROJ-1234",
                   "stories": {"PROJ-1234": {"total_usd": 23.4459, "lower_bound": True, "verified": False}}}, f)
    payload["workspace"] = {"current_dir": repo}

json.dump(payload, sys.stdout)
