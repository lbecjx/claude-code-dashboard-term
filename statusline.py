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

  1. AGENT    model + effort, fast mode, speed of the last response (~N tok/s), usage group (5h / 7d / spend bars), SLOW DOWN, estimated cost,
              and the context window pushed to the right edge (space-between)
  2. SESSION  session name, folder and, only inside a git repo, branch and git user
  3. (opt-in) tokens of the last API call: I / O / R / W

Any missing, null or wrong-typed field simply disappears: no empty separators, no blank lines, no crash.
Usage bars only appear when Claude Code sends the data (Pro/Max limits, or a spend limit behind a gateway).

Environment variables (all optional; a value that is not a number is ignored and the default is used):
  STATUSLINE_ICONS=0       plain text instead of Nerd Font icons
  STATUSLINE_GIT_USER=0    hide the git user (shown by default, only inside a repo)
  STATUSLINE_SPEED=0       hide the speed of the last response (shown by default; reads the end of the local transcript file)
  STATUSLINE_TOKENS=1      add a line with the last call's tokens: I (input) O (output) R (cache read) W (cache write)
  STATUSLINE_FLEX=0        do not push the context to the right edge; keep it next to the first block
  STATUSLINE_MARGIN=N      cells left free on the right in flex mode (default 8, minimum 0). Raise it if the end of line 1 is cut with "…"
  STATUSLINE_ICON_CELLS=2  set to 2 if your terminal draws each icon two cells wide (default 1)
Claude Code exports COLUMNS with the real terminal width, which flex mode uses.
Run `python3 statusline.py --version` to print the version.
"""
import datetime, json, math, os, re, stat, subprocess, sys, time, unicodedata

__version__ = "0.3.1"   # keep in sync with CHANGELOG.md


def env_int(name, default):
    """An integer environment variable; anything that is not an integer falls back to the default."""
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


R = "\033[0m"
# Tone name -> SGR parameters. Plain ANSI numbers follow your terminal theme; "38;5;N" is a fixed 256-color value.
TONE = {"white": 37, "dim": "38;5;248", "green": "38;5;77", "amber": "38;5;220", "red": 31,
        "cyan": 36, "bcyan": 96, "orange": "38;5;172", "mute": "38;5;153",   # mute: light blue for the generic icons
        "faint": "38;5;243"}   # faint: dimmer than dim, for secondary figures such as the speed
# Background colors for the filled part of a bar (the empty part is always ANSI 100).
BG = {"green": "48;5;77", "amber": "48;5;220", "red": 41}

ICONS_ON = os.environ.get("STATUSLINE_ICONS", "1") != "0"
SPEED_ON = os.environ.get("STATUSLINE_SPEED", "1") != "0"
TOKENS_ON = os.environ.get("STATUSLINE_TOKENS", "0") == "1"
GIT_USER_ON = os.environ.get("STATUSLINE_GIT_USER", "1") != "0"
FLEX_ON = os.environ.get("STATUSLINE_FLEX", "1") != "0"
ICON_CELLS = max(1, env_int("STATUSLINE_ICON_CELLS", 1))
# Cells left free on the right: the status row has its own padding, and Claude Code shows its notices there.
MARGIN = max(0, env_int("STATUSLINE_MARGIN", 8))
MIN_SPEED_SECONDS = 0.5   # a shorter span says nothing about speed (and would give absurd numbers)
MAX_SPEED = 99999   # tokens per second; above this the timestamps are not trustworthy
SPEED_TAIL_BYTES = 256 * 1024   # only the end of the transcript is read: it grows with the session and this runs every 30 s
GIT_TIMEOUT = 1   # seconds each git call may take before it is given up
MAX_COLUMNS = 1000   # no real terminal is wider; a bogus COLUMNS must not make the padding enormous
# Variables that would make `git -C <dir>` look at some other repository.
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY")

# Octicons (MIT), shipped inside Nerd Fonts v3. The script only prints the characters; it bundles no font.
# They are written as \u escapes so they stay visible in a diff.
# Do not use oct-zap: it is U+26A1, a standard Unicode character that many terminals draw as an emoji.
ICON = {"name": "\uf412", "branch": "\uf418", "folder": "\uf413", "model": "\uf4bc",
        "context": "\uf472", "usage": "\uf463",
        "alert": "\uf421", "fast": "\uf427", "cost": "\uf439", "reset": "\uf4e3", "user": "\uf415"}
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


# --- reading the payload: every value is checked, so a wrong-typed field is ignored instead of crashing -----------------

def get(d, *keys):
    for k in keys:
        d = d.get(k) if isinstance(d, dict) else None
    return d


def section(d, *keys):
    """A nested object, or {} if it is missing or not an object."""
    v = get(d, *keys)
    return v if isinstance(v, dict) else {}


def num(v):
    """A finite number, or None. Booleans, strings, NaN and infinity are not numbers here."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    try:
        return v if math.isfinite(v) else None
    except OverflowError:   # an integer too large to be a float
        return None


def nonneg(v):
    """A finite number that is not negative, or None."""
    n = num(v)
    return n if n is not None and n >= 0 else None


def pct(v):
    """A percentage rounded half-up to a whole number (never negative, at most 999), or None. The same whole number is
    used for the text, the color and the hints, so the number on screen can never contradict its own color."""
    n = num(v)
    return None if n is None else min(999, int(max(n, 0) + 0.5))


def clean(v):
    """A one-line string, or "". Non-strings are ignored. Dropped: lone surrogates and every control (Cc), format (Cf:
    zero-width, bidi overrides) and line/paragraph separator (Zl, Zp) character, so a value can never inject a newline
    or a terminal escape sequence."""
    if not isinstance(v, str):
        return ""
    s = v.encode("utf-8", "ignore").decode("utf-8")
    return "".join(ch for ch in s if unicodedata.category(ch) not in ("Cc", "Cf", "Zl", "Zp"))


# --- formatting -------------------------------------------------------------------------------------------------------

def human(n):
    """Compact token count: 999, 12.4K, 612K, 1.2M."""
    if n >= 999_500:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 100_000:
        return f"{round(n / 1_000)}K"
    if n >= 1_000:
        return f"{n / 1_000:.1f}".rstrip("0").rstrip(".") + "K"
    return str(int(n))


def time_left(ts):
    s = max(0, int(ts - time.time()))
    d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
    if d > 999:
        return ">999d"
    return f"{d}d{h}h" if d else f"{h}h{m:02d}m" if h else f"{m}m"


def reset_txt(ts):
    """Time until a limit resets, with an hourglass (an arrow in plain-text mode)."""
    sym = icon("reset")
    return paint(f" {sym} {time_left(ts)}" if ICONS_ON else f" {sym}{time_left(ts)}", "dim")


def level_tone(p, warn=60, crit=80):
    return "red" if p >= crit else "amber" if p >= warn else "green"


def cell_bar(p, width, label="", tone=None):
    """Horizontal bar made of per-cell BACKGROUND colors: filled = threshold color, empty = gray.
    `label` is written on top, centered (black over the filled part, white over the empty part)."""
    tone = tone or level_tone(p)
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


# --- git --------------------------------------------------------------------------------------------------------------

def workspace_dir(d):
    """The workspace path exactly as Claude Code sent it: it goes to `git -C`, so it must not be altered. Only the text
    shown on screen is cleaned (see folder_of)."""
    for v in (get(d, "workspace", "current_dir"), d.get("cwd"), get(d, "workspace", "project_dir")):
        if isinstance(v, str) and clean(v):
            return v
    return ""


def git(d, *args):
    """Cleaned stdout of `git -C <workspace> ...`, or "" if there is no directory, git is missing, fails or is too slow."""
    cwd = workspace_dir(d)
    if not cwd:
        return ""
    try:
        env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
        return clean(subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env,
                                    timeout=GIT_TIMEOUT).stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""


def in_git_repo(d):
    return git(d, "rev-parse", "--is-inside-work-tree") == "true"


def branch_of(d):
    return git(d, "branch", "--show-current") or clean(get(d, "worktree", "branch"))


def git_user_of(d):
    return git(d, "config", "user.name")


def folder_of(d):
    path = clean(workspace_dir(d))
    return os.path.basename(path.rstrip("/")) or path


def join(groups):
    return "  ".join(g for g in groups if g)


# --- blocks -----------------------------------------------------------------------------------------------------------

def usage_bar(p, label, window, width, tone=None):
    """One usage bar: the bar with its label inside, the percentage, and the time until it resets."""
    reset = nonneg(window.get("resets_at"))
    return (cell_bar(p, width, label, tone) + " " + paint(f"{p}%", level_tone(p)) +
            (reset_txt(reset) if reset else ""))


def limits(d):
    """Usage group: ONE icon (a gauge) followed by whichever bars exist: 5h, 7d and spend.
    A bar appears only if Claude Code sends its data; if none arrives the whole group (icon included) is hidden.
    Returns a list of parts: that group, plus SLOW DOWN when the 5h window is at 80% or more."""
    # spend_limit only exists behind a Claude apps gateway with a spend limit
    five, week, spend = (section(d, "rate_limits", key) for key in ("five_hour", "seven_day", "spend_limit"))
    five_p, week_p, spend_p = (pct(w.get("used_percentage")) for w in (five, week, spend))
    critical = five_p is not None and five_p >= 80

    bars = []
    if five_p is not None:
        bars.append(usage_bar(five_p, "5h", five, BAR_5H, "red" if critical else None))
    if week_p is not None:
        bars.append(usage_bar(week_p, "7d", week, BAR_WIDTH))
    if spend_p is not None:
        bars.append(usage_bar(spend_p, "spend", spend, BAR_WIDTH))

    parts = []
    if bars:
        lead = paint(f"{icon('usage')} ", "red" if critical else "bcyan") if icon("usage") else ""
        parts.append(lead + "  ".join(bars))
    if critical:
        a = icon("alert")
        parts.append(paint((a + " " if a else "") + "SLOW DOWN", "red"))
    return parts


def context(d):
    ctx_p = pct(get(d, "context_window", "used_percentage"))
    tokens = nonneg(get(d, "context_window", "total_input_tokens"))
    size = nonneg(get(d, "context_window", "context_window_size"))
    ctx = ""
    if tokens is not None and size:
        ctx = f"{human(tokens)}/{human(size)}"
    if ctx_p is not None:
        ctx += (" " if ctx else "") + cell_bar(ctx_p, BAR_WIDTH, f"{ctx_p}%", level_tone(ctx_p))
        # /compact keeps a summary of the conversation; /clear would throw it away, so it is never suggested here.
        # The urgency is carried by the color: dim, then yellow, then red.
        if ctx_p >= 80:
            ctx += " " + paint("/compact", "red")
        elif ctx_p >= 60:
            ctx += " " + paint("/compact", "amber")
        elif ctx_p >= 40:
            ctx += " " + paint("/compact soon", "dim")
    if ctx and icon("context"):
        ctx = paint(icon("context") + " ", "cyan") + ctx
    return ctx


ANSI = re.compile(r"\033\[[0-9;]*m")


def char_width(ch):
    """Terminal cells one character takes: icons ICON_CELLS, combining marks 0, East Asian wide characters 2."""
    cp = ord(ch)
    if 0xE000 <= cp <= 0xF8FF or 0xF0000 <= cp <= 0xFFFFD:   # private-use areas: where Nerd Font icons live
        return ICON_CELLS
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def cells(s):
    """Visible width of a string: ANSI codes stripped, every character counted by the cells it takes."""
    return sum(char_width(ch) for ch in ANSI.sub("", s))


def terminal_columns():
    return min(MAX_COLUMNS, max(0, env_int("COLUMNS", 0)))


def spread(lhs, rhs, cols):
    """`lhs` at the left edge and `rhs` at the right edge of one line. None if they do not fit."""
    if not (lhs and rhs and cols):
        return None
    gap = cols - MARGIN - cells(lhs) - cells(rhs)
    return lhs + " " * gap + rhs if gap >= 2 else None


def model_name(d):
    """Readable model name. A Bedrock or Vertex id (e.g. us.anthropic.claude-sonnet-5-5-20260101-v1:0,
    claude-opus-4-5@20251101, or an ARN) is reduced to "Sonnet 5.5". A name that is already readable is left alone."""
    raw = clean(get(d, "model", "display_name")) or clean(get(d, "model", "id"))
    n = re.sub(r"\[[^\]]*\]$", "", raw.rsplit("/", 1)[-1])               # ARN: keep what follows the last "/"; drop a "[1m]" suffix
    if "anthropic" not in n and not n.startswith("claude-"):
        return raw
    n = re.sub(r"^(?:us-gov|us|eu|apac|ap|global|jp|au|ca)\.", "", n)   # inference-profile region prefix
    n = re.sub(r"^anthropic\.", "", n)
    n = re.sub(r"-v\d+(?::\d+)?$", "", n)                                # version suffix: -v1:0
    n = re.sub(r"[-@]\d{8}$", "", n)                                     # date: -20260101 (Bedrock) or @20260101 (Vertex)
    n = re.sub(r"^claude-", "", n)
    words = [t for t in n.split("-") if t.isalpha()]
    nums = [t for t in n.split("-") if t.isdigit()]
    if not words:
        return raw
    return " ".join(w.capitalize() for w in words) + (" " + ".".join(nums) if nums else "")


def transcript_rows(path):
    """The JSON objects in the last SPEED_TAIL_BYTES of a transcript file (one per line). A line that does not parse, and
    the first line when the read starts in the middle of one, are skipped. An unreadable file gives no rows."""
    try:
        # O_NONBLOCK: opening a pipe that someone swapped in must not wait for a writer
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0))
        with os.fdopen(fd, "rb") as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):   # a pipe or device could block or never end
                return []
            start = max(0, f.seek(0, os.SEEK_END) - SPEED_TAIL_BYTES - 1)   # one byte before the window, to see where a line begins
            f.seek(start)
            data = f.read(SPEED_TAIL_BYTES + 1)
    except (OSError, ValueError):
        return []
    if start > 0:   # the read began inside a line unless the byte before the window is a line break
        data = data[1:] if data[:1] == b"\n" else data.partition(b"\n")[2]
    rows = []
    for line in data.split(b"\n"):
        try:
            row = json.loads(line.decode("utf-8", "replace"))
        except (ValueError, RecursionError):   # RecursionError: a line nested absurdly deep
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def timestamp(v):
    """Seconds since the epoch for an ISO 8601 UTC string such as 2026-10-08T06:31:30.461Z, or None.
    The fraction is normalized to six digits because Python 3.9 only accepts three or six."""
    if not isinstance(v, str):
        return None
    m = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)", v)
    if not m:
        return None
    try:
        return datetime.datetime.fromisoformat(
            m.group(1) + "." + (m.group(2) or "0").ljust(6, "0")[:6] + m.group(3).replace("Z", "+00:00")).timestamp()
    except (ValueError, OverflowError, OSError):
        return None


def tokens_per_second(d):
    """(speed, stale) for the last response, or None. Speed: the output tokens of its API calls divided by the seconds
    the model spent on them. Each call is timed from the row before it (the prompt or the tool result it answers) to its last row, so time
    spent running tools is not counted, but the wait for the first token is, and the speed is understated. A call written
    in several rows is counted once by its id. When the newest response has no call yet, or cannot be timed or gives an
    implausible value, the response before it is used and stale is True."""
    path = clean(d.get("transcript_path"))
    if not path:
        return None
    since, responses, seen = None, [[]], {}   # since: time of the newest user or assistant row
    for row in transcript_rows(path):
        if row.get("isSidechain") is True or row.get("type") not in ("user", "assistant"):
            continue
        at = timestamp(row.get("timestamp"))
        msg = section(row, "message")
        if row.get("type") == "user":
            if isinstance(msg.get("content"), str) and row.get("isMeta") is not True:   # a prompt, not a tool result
                responses.append([])
            since = at
            continue
        out = nonneg(get(msg, "usage", "output_tokens"))
        call_id = clean(msg.get("id"))
        if at is not None and out and call_id:   # no id: its rows cannot be grouped; 0 tokens: an error row, not a reply
            call = seen.get(call_id)   # a later row of a known call extends it, even after a prompt row
            if call:
                call[1], call[2] = max(call[1], at), float(out)
            else:
                call = seen[call_id] = [since, at, float(out)]   # start None: the row before it is unknown, so not timed
                responses[-1].append(call)
        since = at if at is not None else since
    for age, response in enumerate(reversed(responses)):   # the newest response that can be measured; an older one rather than nothing
        calls = [c for c in response if c[0] is not None and c[1] > c[0]]
        tokens, seconds = sum(c[2] for c in calls), sum(c[1] - c[0] for c in calls)
        speed = tokens / seconds if seconds >= MIN_SPEED_SECONDS else None
        if speed is not None and math.isfinite(speed) and 0.5 <= speed <= MAX_SPEED:   # shows as 1 to MAX_SPEED
            return speed, age > 0
    return None


def block_speed(d):
    """Speed of the last response, rounded once: shown as ~N tok/s, as "… tok/s" while the newest response cannot be
    measured yet (the value would belong to an older one), or nothing when it is off or cannot be computed."""
    if not SPEED_ON:
        return ""
    result = tokens_per_second(d)
    if result is None:
        return ""
    speed, stale = result
    return paint("\u2026 tok/s" if stale else f"~{int(speed + 0.5)} tok/s", "faint")


def block_model(d):
    model = model_name(d)
    effort = clean(get(d, "effort", "level"))
    model_txt = tagged("model", model, "amber" if model.startswith("Opus") else "cyan") if model else ""
    effort_txt = paint(effort, "amber" if effort in ("high", "xhigh", "max") else "dim") if effort else ""
    head = model_txt + (" " + effort_txt if model_txt and effort_txt else effort_txt)   # model and effort, joined
    fast_txt = (paint(icon("fast") + " ", "orange") + paint("fast", "orange")) if d.get("fast_mode") is True else ""
    return join([head, fast_txt, safe(block_speed, d), *limits(d), block_cost(d)])


def block_session(d):
    name = clean(d.get("session_name"))
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
    cost = nonneg(get(d, "cost", "total_cost_usd"))
    if cost is None or cost < 0.005:   # nothing to show until it reaches a cent
        return ""
    i = icon("cost")
    return (paint(i + " ", "mute") if i else "") + paint(f"${cost:.2f} eq", "dim")


def block_tokens(d):
    """I = fresh input, O = output, R = cache read, W = cache write (last API call)."""
    cu = get(d, "context_window", "current_usage")
    if not (TOKENS_ON and isinstance(cu, dict)):
        return ""
    count = lambda key: human(nonneg(cu.get(key)) or 0)
    return join([
        paint("I", "dim") + f" {count('input_tokens')}",
        paint("O", "dim") + f" {count('output_tokens')}",
        paint("R", "dim") + f" {count('cache_read_input_tokens')}",
        paint("W", "dim") + f" {count('cache_creation_input_tokens')}",
    ])


def safe(render, d):
    """Render one block; if anything unexpected goes wrong, that block is left out instead of killing the status line."""
    try:
        return render(d)
    except Exception:
        return ""


def main():
    if "--version" in sys.argv[1:]:
        print(f"claude-code-dashboard-term {__version__}")
        return
    try:
        # parse_int=float: an absurdly long integer becomes infinity (ignored by num()) instead of failing the whole parse
        d = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace"), parse_int=float)
    except Exception:   # deliberately broad: whatever arrives, the status line must not die
        d = {}
    if not isinstance(d, dict):
        d = {}
    try:
        sys.stdout.reconfigure(errors="replace")   # an unencodable character becomes "?" instead of a crash
    except (AttributeError, ValueError):
        pass
    model_line, session_line, context_line = safe(block_model, d), safe(block_session, d), safe(context, d)
    # <agent block> <context> with space-between: context at the right edge of line 1.
    # If COLUMNS is unknown or the line does not fit, the context stays on the same line, next to the block.
    first = (FLEX_ON and spread(model_line, context_line, terminal_columns())) or join([model_line, context_line])
    try:
        for line in (first, session_line, safe(block_tokens, d)):
            if line:
                print(line)
        sys.stdout.flush()
    except BrokenPipeError:   # the reader went away early: stop quietly, with no traceback at exit
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except OSError:
            pass


if __name__ == "__main__":
    main()
