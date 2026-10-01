#!/usr/bin/env python3
# claude-code-dashboard-term — a status line for Claude Code: model, usage limits, cost, context and git
# https://github.com/lbecjx/claude-code-dashboard-term
# Copyright (C) 2026  lbecjx
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See LICENSE for the full text.
"""Claude Code status line: reads the session JSON on stdin, prints up to three lines.

  1. AGENT    model + effort, fast mode, usage group (5h / 7d / spend bars), SLOW DOWN, estimated cost,
              and the context window pushed to the right edge (space-between)
  2. SESSION  session name, folder and, only inside a git repo, branch and git user
  3. (opt-in) tokens of the last API call: I / O / R / W

Any missing or null field simply disappears: no empty separators, no blank lines.
Usage bars only appear when Claude Code sends the data (Pro/Max limits, or a spend limit behind a gateway).

Environment variables (all optional):
  STATUSLINE_ICONS=0       plain text instead of Nerd Font icons
  STATUSLINE_GIT_USER=0    hide the git user (shown by default, only inside a repo)
  STATUSLINE_TOKENS=1      add a line with the last call's tokens: I (input) O (output) R (cache read) W (cache write)
  STATUSLINE_FLEX=0        do not push the context to the right edge; keep it next to the first block
  STATUSLINE_MARGIN=N      cells left free on the right in flex mode (default 8). Raise it if the end of line 1 is cut with "…"
  STATUSLINE_ICON_CELLS=2  set to 2 if your terminal draws each icon two cells wide (default 1)
Claude Code exports COLUMNS with the real terminal width, which flex mode uses.
"""
import json, os, re, subprocess, sys, time

R = "\033[0m"
# Tone name -> SGR parameters. Plain ANSI numbers follow your terminal theme; "38;5;N" is a fixed 256-color value.
TONE = {"white": 37, "dim": "38;5;248", "green": "38;5;77", "amber": "38;5;220", "red": 31,
        "cyan": 36, "bcyan": 96, "orange": "38;5;172", "mute": "38;5;153"}   # mute: light blue for the generic icons
# Background colors for the filled part of a bar (the empty part is always ANSI 100).
BG = {"green": "48;5;77", "amber": "48;5;220", "red": 41}

ICONS_ON = os.environ.get("STATUSLINE_ICONS", "1") != "0"
TOKENS_ON = os.environ.get("STATUSLINE_TOKENS", "0") == "1"
GIT_USER_ON = os.environ.get("STATUSLINE_GIT_USER", "1") != "0"
FLEX_ON = os.environ.get("STATUSLINE_FLEX", "1") != "0"
ICON_CELLS = int(os.environ.get("STATUSLINE_ICON_CELLS", "1"))
# Cells left free on the right: the status row has its own padding, and Claude Code shows its notices there.
MARGIN = int(os.environ.get("STATUSLINE_MARGIN", "8"))

# Octicons (MIT), shipped inside Nerd Fonts v3. The script only prints the characters; it bundles no font.
# Do not use oct-zap: it is U+26A1, a standard Unicode character that many terminals draw as an emoji.
ICON = {"name": "", "branch": "", "folder": "", "model": "",
        "context": "", "usage": "",
        "alert": "", "fast": "", "cost": "", "reset": "", "user": ""}
TEXT = {"name": "", "branch": "", "folder": "", "model": "", "context": "",
        "usage": "", "alert": "", "fast": "⚡", "cost": "", "reset": "→", "user": ""}

BAR_WIDTH = 6    # 7d, spend and context bars, in cells
BAR_5H = 10      # the 5h bar is wider


def icon(name):
    return (ICON if ICONS_ON else TEXT)[name]


def paint(text, tone="white"):
    return f"\033[{TONE[tone]}m{text}{R}"


def tagged(name, text, tone, icon_tone=None):
    """Icon (if any) + text. The icon uses icon_tone when given, otherwise the text's tone."""
    i = icon(name)
    return (paint(i + " ", icon_tone or tone) if i else "") + paint(text, tone)


def get(d, *keys):
    for k in keys:
        d = d.get(k) if isinstance(d, dict) else None
    return d


def human(n):
    if n >= 1_000_000:
        v = n / 1_000_000
        return f"{v:g}M" if v == int(v) else f"{v:.1f}M"
    if n >= 100_000:
        return f"{round(n / 1_000)}K"
    if n >= 1_000:
        return f"{n / 1_000:.1f}".rstrip("0").rstrip(".") + "K"
    return str(int(n))


def reset_txt(ts):
    """Time until a limit resets, with an hourglass (an arrow in plain-text mode)."""
    sym = icon("reset")
    return paint(f" {sym} {left(ts)}" if ICONS_ON else f" {sym}{left(ts)}", "dim")


def left(ts):
    s = max(0, int(ts - time.time()))
    d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
    return f"{d}d{h}h" if d else f"{h}h{m:02d}m" if h else f"{m}m"


def level_tone(p, warn=50, crit=80):
    return "red" if p >= crit else "amber" if p >= warn else "green"


def cell_bar(p, width, label="", tone=None):
    """Horizontal bar made of per-cell BACKGROUND colors: filled = threshold color, empty = gray.
    `label` is written on top, centered (black over the filled part, white over the empty part)."""
    tone = tone or level_tone(p, 60)
    filled = round(max(0, min(100, p)) / 100 * width)
    if p > 0 and filled == 0:
        filled = 1   # a little usage must not look like none: always paint at least one cell
    label = label[:width]
    start = (width - len(label)) // 2
    cells = []
    for i in range(width):
        ch = label[i - start] if label and start <= i < start + len(label) else " "
        on = i < filled
        cells.append(f"\033[{30 if on else 97};{BG[tone] if on else 100}m{ch}")
    return "".join(cells) + R


def workspace_dir(d):
    return get(d, "workspace", "current_dir") or d.get("cwd") or "."


def in_git_repo(d):
    """True only if the current directory is inside a git work tree and git answers."""
    try:
        out = subprocess.run(["git", "-C", workspace_dir(d), "rev-parse", "--is-inside-work-tree"],
                             capture_output=True, text=True, timeout=1).stdout.strip()
        return out == "true"
    except Exception:
        return False


def branch_of(d):
    try:
        out = subprocess.run(["git", "-C", workspace_dir(d), "branch", "--show-current"],
                             capture_output=True, text=True, timeout=1).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    return get(d, "worktree", "branch") or ""


def git_user_of(d):
    """git config user.name. Empty if unset or git does not answer."""
    try:
        return subprocess.run(["git", "-C", workspace_dir(d), "config", "user.name"],
                              capture_output=True, text=True, timeout=1).stdout.strip()
    except Exception:
        return ""


def folder_of(d):
    path = get(d, "workspace", "current_dir") or d.get("cwd") or get(d, "workspace", "project_dir") or ""
    return os.path.basename(path.rstrip("/")) or path


def join(groups):
    return "  ".join(g for g in groups if g)


def limits(d):
    """Usage group: ONE icon (a gauge) followed by whichever bars exist: 5h, 7d and spend.
    A bar appears only if Claude Code sends its data; if none arrives the whole group (icon included) is hidden.
    Also returns SLOW DOWN when the 5h window is at 80% or more."""
    five = get(d, "rate_limits", "five_hour") or {}
    week = get(d, "rate_limits", "seven_day") or {}
    spend = get(d, "rate_limits", "spend_limit") or {}   # only behind a Claude apps gateway with a spend limit
    five_p, week_p, spend_p = five.get("used_percentage"), week.get("used_percentage"), spend.get("used_percentage")
    critical = five_p is not None and five_p >= 80

    def bar(p, label, window, tone=None):
        reset = window.get("resets_at")
        return (cell_bar(p, BAR_5H if label == "5h" else BAR_WIDTH, label, tone) + " " +
                paint(f"{p:.0f}%", level_tone(p)) + (reset_txt(reset) if reset else ""))

    bars = []
    if five_p is not None:
        bars.append(bar(five_p, "5h", five, "red" if critical else None))
    if week_p is not None:
        bars.append(bar(week_p, "7d", week))
    if spend_p is not None:
        bars.append(bar(spend_p, "spend", spend))

    parts = []
    if bars:
        lead = paint(f"{icon('usage')} " if icon("usage") else "", "red" if critical else "bcyan")
        parts.append(lead + "  ".join(bars))
    if critical:
        a = icon("alert")
        parts.append(paint((a + " " if a else "") + "SLOW DOWN", "red"))
    return parts


def context(d):
    ctx_p = get(d, "context_window", "used_percentage")
    tokens = get(d, "context_window", "total_input_tokens")
    size = get(d, "context_window", "context_window_size")
    ctx = ""
    if tokens is not None and size:
        ctx = f"{human(tokens)}/{human(size)}"
    if ctx_p is not None:
        ctx += (" " if ctx else "") + cell_bar(ctx_p, BAR_WIDTH, f"{ctx_p:.0f}%", level_tone(ctx_p, 60))
        if ctx_p >= 80:
            ctx += " " + paint("/clear", "red")
        elif ctx_p >= 60:
            ctx += " " + paint("/compact", "amber")
        elif ctx_p >= 40:
            ctx += " " + paint("/compact soon", "dim")
    if ctx and icon("context"):
        ctx = paint(icon("context") + " ", "cyan") + ctx
    return ctx


ANSI = re.compile(r"\033\[[0-9;]*m")
PUA = re.compile("[-\U000f0000-\U000ffffd]")   # private-use area: where Nerd Font icons live


def cells(text):
    """Visible width: ANSI codes stripped, each icon counted as ICON_CELLS cells."""
    plain = ANSI.sub("", text)
    return len(plain) + len(PUA.findall(plain)) * (ICON_CELLS - 1)


def terminal_columns():
    try:
        return int(os.environ.get("COLUMNS", ""))
    except ValueError:
        return 0


def spread(left, right, cols):
    """`left` at the left edge and `right` at the right edge of one line. None if they do not fit."""
    if not (left and right and cols):
        return None
    gap = cols - MARGIN - cells(left) - cells(right)
    return left + " " * gap + right if gap >= 2 else None


def model_name(d):
    """Readable model name. A Bedrock id (e.g. us.anthropic.claude-sonnet-5-5-20260101-v1:0, or an ARN)
    is reduced to "Sonnet 5.5". A name that is already readable is left alone."""
    raw = get(d, "model", "display_name") or get(d, "model", "id") or ""
    n = raw.rsplit("/", 1)[-1]                                           # ARN: keep what follows the last "/"
    if "anthropic" not in n and not n.startswith("claude-"):
        return raw
    n = re.sub(r"^(?:us-gov|us|eu|apac|ap|global|jp|au|ca)\.", "", n)   # inference-profile region prefix
    n = re.sub(r"^anthropic\.", "", n)
    n = re.sub(r"-v\d+(?::\d+)?$", "", n)                                # version suffix: -v1:0
    n = re.sub(r"-\d{8}$", "", n)                                        # date: -20260101
    n = re.sub(r"^claude-", "", n)
    words = [t for t in n.split("-") if t.isalpha()]
    nums = [t for t in n.split("-") if t.isdigit()]
    if not words:
        return raw
    return " ".join(w.capitalize() for w in words) + (" " + ".".join(nums) if nums else "")


def block_model(d):
    model = model_name(d)
    effort = get(d, "effort", "level")
    model_txt = tagged("model", model, "amber" if model.startswith("Opus") else "cyan") if model else ""
    effort_txt = paint(effort, "amber" if effort in ("high", "xhigh", "max") else "dim") if effort else ""
    head = model_txt + (" " + effort_txt if model_txt and effort_txt else effort_txt)   # model and effort, joined
    fast_txt = (paint(icon("fast") + " ", "orange") + paint("fast", "orange")) if d.get("fast_mode") else ""
    return join([head, fast_txt, *limits(d), block_cost(d)])


def block_session(d):
    name = d.get("session_name") or ""
    repo = in_git_repo(d)
    br = branch_of(d) if repo else ""
    folder = folder_of(d)
    user = git_user_of(d) if (repo and GIT_USER_ON) else ""   # switched off: git is not even called
    return join([
        tagged("name", name, "white") if name else "",
        tagged("folder", folder, "dim", "mute") if folder else "",
        tagged("branch", br, "dim", "mute") if br else "",
        tagged("user", user, "dim", "mute") if user else "",
    ])


def block_cost(d):
    """Estimated session cost at list price. Not what a subscription bills, hence the "eq" (equivalent)."""
    cost = get(d, "cost", "total_cost_usd")
    if not cost:
        return ""
    i = icon("cost")
    txt = (paint(i + " ", "mute") if i else "") + paint(f"${cost:.2f} eq", "dim")
    if model_name(d).startswith("Opus"):
        txt += " " + paint("(~2x)", "amber")   # Opus is priced about twice as much per token as Sonnet
    return txt


def block_tokens(d):
    """I = fresh input, O = output, R = cache read, W = cache write (last API call)."""
    cu = get(d, "context_window", "current_usage")
    if not (TOKENS_ON and isinstance(cu, dict)):
        return ""
    return join([
        paint("I", "dim") + f" {human(cu.get('input_tokens') or 0)}",
        paint("O", "dim") + f" {human(cu.get('output_tokens') or 0)}",
        paint("R", "dim") + f" {human(cu.get('cache_read_input_tokens') or 0)}",
        paint("W", "dim") + f" {human(cu.get('cache_creation_input_tokens') or 0)}",
    ])


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        d = {}
    if not isinstance(d, dict):
        d = {}
    model_line, session_line, context_line = block_model(d), block_session(d), context(d)
    # <agent block> <context> with space-between: context at the right edge of line 1.
    # If COLUMNS is unknown or the line does not fit, the context stays on the same line, next to the block.
    first = (FLEX_ON and spread(model_line, context_line, terminal_columns())) or join([model_line, context_line])
    for line in (first, session_line, block_tokens(d)):
        if line:
            print(line)


if __name__ == "__main__":
    main()
