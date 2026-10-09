# claude-code-dashboard-term

> **Repository:** <https://github.com/lbecjx/claude-code-dashboard-term>

A compact, colored **status line for [Claude Code](https://code.claude.com)**. One small Python script that turns the session data Claude Code already gives you into a dashboard at the bottom of your terminal: which model and effort you are on, how much of your usage windows you have burned, the estimated cost, how full the context is, and where you are in git.

![claude-code-dashboard-term running in Ghostty while Claude works: model and effort, speed and workflow-dev story cost on the left, 5h and 7d usage bars with reset times, estimated session cost and context window on the right, and session, folder, git branch and user on the second line](docs/screenshot.png)

*The status line in [Ghostty](https://ghostty.org), while Claude is answering. Line 1: model and effort, speed of the last response and the workflow-dev story cost on the left; the 5-hour and 7-day usage bars, estimated session cost and context window pushed to the right. Line 2: session name, folder, git branch and git user. The bars are drawn with colored cell backgrounds, with the percentage written on top.*

## Get started with Claude

The fastest way: paste the prompt below into Claude Code and let it do the whole install. It inspects your setup, shows you **one plan** listing everything it will change (including the icon font, when needed), and after a single OK it does all of it, with a backup of every file and setting it touches. Your terminal font is never replaced unless you pick a new one yourself, from a list with previews. Claude Code may still ask you to allow each command it runs; just answer OK.

````text
Install the "claude-code-dashboard-term" status line for me. Do all of it yourself: I only want to read your questions and answer OK. Work in two phases.

PHASE 1: inspect (read-only, no questions)
1. Check that `python3` is available (on Windows, `python`) and that it is 3.9 or newer.
2. Detect my operating system and my terminal (for example from $TERM_PROGRAM, $WT_SESSION or the parent process).
   Read ~/.claude/settings.json and check whether there is already a "statusLine" entry or a ~/.claude/statusline.py file.
3. Download the script to a temporary file from
   https://github.com/lbecjx/claude-code-dashboard-term/releases/latest/download/statusline.py
   and read it yourself. It must only read stdin, the end of the local transcript file named in `transcript_path` (read-only) and, in the current git repository, the workflow-dev cost index `.workflow-dev/context/.usage/.index.json` and the current story's status in `.workflow-dev/context/<ID>.md` or `local-backlog/<ID>-*.md` (read-only), print to stdout and call local `git`, with no network access and without writing any file.
   If it does anything else, stop and tell me.
4. Decide whether my terminal needs the Nerd Font icons. If it is Ghostty, it does not: skip every font step (7 and the
   question in 9), do not ask me anything about fonts and do not install any font. Most other terminals do, with the
   caveats in step 7. My font must stay exactly as it is unless I choose a new one myself: the goal is to ADD the
   icons, not to replace my font. Write down my current terminal font setting (name and size) now, before anything
   is changed, so it can be restored.
   If my terminal is macOS Terminal, I choose the font now, in this phase, so that the plan already names it:
   a. Open in my browser the preview of each font you will offer, with `open https://www.programmingfonts.org/#<id>`
      (the ids are the "Full Preview" links of each font at https://www.nerdfonts.com/font-downloads: for example
      cascadia-code, meslo, jetbrainsmono, firacode, hack). A question widget cannot draw a font and a text list shows
      me nothing, so I must be able to see them for real before choosing. Open the recommended font LAST, so that its
      tab is the one I am looking at when you ask. In the question, say the order of the tabs (for example "tab 1
      Meslo, tab 2 JetBrainsMono, tab 3 Cascadia") and that these previews show the letters of each font, not the
      icons, whose size I can only judge once a font is applied.
   b. Then ask me ONE selection question with explicit options, never free text: keep my current font and use plain
      text (STATUSLINE_ICONS=0), "CaskaydiaCove Nerd Font" (Cascadia Code with the icons) marked as the recommended
      one, and one or two more, including one that resembles my current font if there is one. The question tool adds
      an "Other" option for any font I name myself. Do not choose for me: the recommendation is only a suggestion.

Then give me ONE plan and ask for ONE approval. The plan lists everything you will change: each file you will create
or modify with its timestamped backup path (for example ~/.claude/statusline.py.bak-YYYYMMDD-HHMMSS), any package
you will install, any terminal setting you will change, and the exact block you will add to settings.json:
  "statusLine": { "type": "command", "command": "python3 ~/.claude/statusline.py", "refreshInterval": 30 }

PHASE 2: do it (after my OK, without asking again)
5. Make the backups, then install the script at ~/.claude/statusline.py.
6. Merge the "statusLine" block into ~/.claude/settings.json without removing anything else.
7. Icons need a font that has them, and I do NOT want my terminal font replaced. What to do depends on my terminal:
   - Ghostty: this whole step does not apply; it already has the icons.
   - macOS Terminal: it only draws the characters of the profile font, so a symbols font would change nothing and real
     icons need a complete Nerd Font as the profile font, which changes the font I see. Apply the choice I made in
     step 4. If I chose plain text, add STATUSLINE_ICONS=0 to the command and install nothing. If I chose a font,
     install only that one (Homebrew casks are named font-<name>-nerd-font; `brew search nerd-font` lists them) and use
     its regular variant (for example "CaskaydiaCove Nerd Font", PostScript name CaskaydiaCoveNF-Regular), not the
     "Mono" variant, which shrinks every icon to fit one cell and makes them look tiny. Check the exact font name the
     system reports after installing, set it as the font of my current profile only, keep my current font size, and tell
     me my original font and exactly how to go back. Offer to restore it if I do not like the result. If the icons
     then overlap the text, switch to the Mono variant or set STATUSLINE_ICON_CELLS=2.
   - Terminals that accept a font list (Windows Terminal, VS Code): install only the "Symbols Nerd Font" (the
     symbols-only font, not a complete Nerd Font) with the package manager of my system (Homebrew:
     `brew install --cask font-symbols-only-nerd-font`) or from
     https://github.com/ryanoasis/nerd-fonts/releases/latest/download/NerdFontsSymbolsOnly.zip, and add it as a
     fallback entry AFTER my current font, never replacing it. Include that setting in the plan.
   - Any other terminal: install the symbols font, open a new window and check; if the icons are boxes, do not switch
     my font: use STATUSLINE_ICONS=0 and tell me.
   Unless I picked a new font myself in the macOS Terminal option, my font setting must end exactly as it was: if you
   changed it at all (even temporarily, for a test), restore the value you wrote down in step 4, check that it was
   restored, and tell me.
8. Test the script: download demo.py from
   https://github.com/lbecjx/claude-code-dashboard-term/releases/latest/download/demo.py to a temporary file and run
     python3 /tmp/demo.py | COLUMNS=140 python3 ~/.claude/statusline.py
   Show me the output.
9. You cannot see my screen, so ask me this one question. The icon characters cannot be shown in your own text, so
   tell me to run this line myself by typing `! ` (an exclamation mark and a space) before it, and ask whether I see
   icons or boxes, and whether the icons are a readable size.
   python3 -c "print('\uf412 \uf413 \uf418 \uf4bc \uf4e3 \uf439 \uf4a0 \uf469')"
   Skip this question if my terminal is Ghostty or you already chose plain text. A new terminal window may be needed for a newly installed font to be picked up. If I still see boxes, question marks or nothing,
   set STATUSLINE_ICONS=0 in the command ("command": "STATUSLINE_ICONS=0 python3 ~/.claude/statusline.py").
10. Finish with a short summary of what you changed, how to undo it (restore the backups), and that the status line
    updates within about 30 seconds, without restarting Claude Code.

Rules: change nothing that is not in the plan. Never leave my terminal font different from how you found it, except for a complete Nerd Font that I picked myself in step 7. Do not use sudo without telling me first. If a step fails, try to
fix it once; if it still fails, stop and explain.
````

> The prompt downloads `statusline.py` and `demo.py` from the latest release of <https://github.com/lbecjx/claude-code-dashboard-term/releases>. If you forked the repo, replace `lbecjx/claude-code-dashboard-term` in the two URLs with your own (your fork needs a release of its own), or tell Claude to copy `statusline.py` from your local clone instead.

## Manual install

Requirements: Python 3.9 or newer (the CI runs 3.9, 3.12 and the latest 3.x), and a Claude Code recent enough to support custom status lines. `git` is optional (without it, branch and user are simply not shown).

1. **Get the script.** Download `statusline.py` from the latest release:

   ```bash
   mkdir -p ~/.claude
   curl -L -o ~/.claude/statusline.py https://github.com/lbecjx/claude-code-dashboard-term/releases/latest/download/statusline.py
   ```

   Or clone the repository, to read the code or to use `examples/demo.py`, and copy the file. A clone is the development version, which can be ahead of the latest release; run `git checkout <tag>` for a released one.

   ```bash
   git clone https://github.com/lbecjx/claude-code-dashboard-term.git
   cd claude-code-dashboard-term
   mkdir -p ~/.claude
   cp statusline.py ~/.claude/statusline.py
   ```

2. **Register it** in `~/.claude/settings.json` (Windows: `%USERPROFILE%\.claude\settings.json`). Add the `statusLine` block, keeping whatever else the file already has:

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python3 ~/.claude/statusline.py",
       "refreshInterval": 30
     }
   }
   ```

   `refreshInterval` (seconds) keeps the reset countdowns moving while you are idle. Claude Code reloads settings automatically, so there is no need to restart.

3. **Check that it works** without a live session, see [Try it without a live session](#try-it-without-a-live-session).

4. **If the icons look wrong** (boxes or `?`), follow [Icons and Nerd Fonts](#icons-and-nerd-fonts) or switch to plain text with `STATUSLINE_ICONS=0`.

> Only tested on macOS so far. It should work anywhere Claude Code and Python 3 run, but Windows has not been tried: use `python` instead of `python3` there if that is what your system provides.

## Contents

- [Get started with Claude](#get-started-with-claude)
- [Manual install](#manual-install)
- [At a glance](#at-a-glance)
- [What each part means](#what-each-part-means)
- [Icons and Nerd Fonts](#icons-and-nerd-fonts)
- [Configuration](#configuration)
- [Colors and thresholds](#colors-and-thresholds)
- [Providers](#providers)
- [Try it without a live session](#try-it-without-a-live-session)
- [Troubleshooting](#troubleshooting)
- [Versioning](#versioning)
- [Issues and contributions](#issues-and-contributions)
- [Uninstall](#uninstall)
- [Privacy and safety](#privacy-and-safety)
- [Attribution and licenses](#attribution-and-licenses)
- [License](#license)

## At a glance

- **No dependencies.** One file, Python 3 standard library only.
- **No network.** It only reads the JSON Claude Code sends on stdin, the end of your local session transcript (read-only, for the speed) and, in a project that uses [workflow-dev](https://github.com/lbecjx/workflow-dev), that project's story cost index and the status of the current story, and, optionally, asks local `git` for the branch and user. It writes no files: it only prints.
- **Hides what does not apply.** No usage limits from your provider? The usage group disappears. Not in a git repo? No branch, no user.
- **Fast.** A run takes a few tens of milliseconds.

## What each part means

**Line 1 — the agent**

On the left, what describes the agent and the task: model and effort, fast mode, speed and the story cost. Pushed to the right edge, what measures consumption: the usage group, the session cost and the context window, each split from the next by a thin `│`. When the terminal is too narrow (or with `STATUSLINE_FLEX=0`), the right group follows the left one on the same line, in the same order.

| Part | Meaning |
|---|---|
| `Sonnet 5.5 medium` | Model and reasoning effort. The effort is gray for `low` and `medium`, and **yellow** for `high`, `xhigh` and `max`, because those use your usage faster. `Opus` is yellow too. A Bedrock model id such as `us.anthropic.claude-sonnet-5-5-20260101-v1:0` is shortened to `Sonnet 5.5`. |
| `fast` | Shown only while Claude Code's fast mode is on. |
| `~126 tok/s` | **Approximate** speed of the last response, in output tokens per second: the output tokens of all its model calls divided by the time the model spent on them. Time spent running tools is not counted, but each call **includes the wait for the first token**, so the value is understated, most of all for short responses. Claude Code does not report stream timings, so it is computed from the timestamps in the session transcript. While a new response has no model call yet, or one too short to time, the number is replaced by `… tok/s` until the new response is measured. It has its own pulse icon. Nothing is shown only before the first response of the session. Turn it off with `STATUSLINE_SPEED=0`. |
| `PROJ-1234 ≥$23.45` | Cost of the **current [workflow-dev](#workflow-dev-story-cost) story**, across every session that worked on it: a different number from the session cost (`$31.23 eq`) on the right. `≥` when the real cost may be higher (part of it is an estimate). Only in a project that uses workflow-dev, on a branch named after the story, while the story is open (see [workflow-dev story cost](#workflow-dev-story-cost)). |
| `Rolling` · `Weekly` · `Budget` | The **usage group**: one window per bar that exists, each with its word and split from the next by a `│`. `Rolling` is the 5-hour window, `Weekly` the 7-day window (both from your subscription), `Budget` a gateway spend limit. Each bar has the percentage used written inside it, followed by the time until it resets. The bar is one cell wider when that keeps the percentage centered. |
| `$31.23 eq` | Estimated cost of the **current session** at API list prices (Claude Code's `cost.total_cost_usd`). It starts at $0 with every new session, including after `/clear`; it is **not** a daily or weekly total. **Not what you are billed**: on a subscription nothing is billed per token, hence "eq" (equivalent). |
| `▓▓▓▓░░ 61% 613K/1M` | Context window: a bar with the percentage inside, then the tokens used out of the window size (the same order as the usage windows: icon, bar, text). At 40% you get a dim `/compact soon`, at 60% `/compact`, and from 80% the same `/compact` in red (`/compact` keeps a summary of the conversation; the urgency is carried by the color). Last part of the line, at the right edge. |

**Line 2 — the session**

| Part | Meaning |
|---|---|
| tag | Session name (set with `claude --name` or `/rename`, otherwise the AI-generated title). Missing until one exists. |
| folder | Name of the current directory. |
| branch | Current git branch. **Only inside a git repository.** |
| person | `git config user.name`. **Only inside a git repository**, and you can turn it off. |

**Line 3 — tokens (off by default)**: `I` fresh input, `O` output, `R` cache read, `W` cache write, for the last API call. Turn it on with `STATUSLINE_TOKENS=1`.

## Icons and Nerd Fonts

The icons are [Octicons](https://primer.style/foundations/icons) (GitHub's icon set) as they ship **inside [Nerd Fonts](https://www.nerdfonts.com) v3**. The script does not bundle any font: it only prints the characters. Whether you see an icon or a box depends on the font your terminal uses.

| Your terminal | What to do |
|---|---|
| **[Ghostty](https://ghostty.org)** | Nothing. It embeds the Nerd Font symbols and falls back to them for any missing character. If the icons look small, see [Ghostty: full-size icons with your own font](#ghostty-full-size-icons-with-your-own-font). |
| **macOS Terminal** | It only draws the characters of the profile font and does not fall back to another font, so a symbols font does not help. Choose a complete Nerd Font as the profile font (see the alternative below, with a preview of each one), which changes your font, or keep your font and use plain text with `STATUSLINE_ICONS=0`. |
| **Windows Terminal, VS Code** | Install the **Symbols Nerd Font** (symbols only) and add it as a fallback after your font. Your own font stays, as described below. |
| **Anything else** (iTerm2, GNOME Terminal, ...) | Install the Symbols Nerd Font and open a new window. If the icons show, nothing else is needed; if they are boxes, use plain text or the alternative below. |
| Do not want to install anything | Use plain text: `STATUSLINE_ICONS=0`. |

### 1. Install the symbols font

The **Symbols Nerd Font** contains only the icons, so it does not replace any letter of your font. Some terminals use an installed font for the characters their own font does not have, so after installing it and opening a new window the icons appear without changing any setting. macOS Terminal does not: it only draws the profile font.

**macOS (Homebrew)**

```bash
brew install --cask font-symbols-only-nerd-font
```

**Windows, Linux, or macOS without Homebrew**

Download <https://github.com/ryanoasis/nerd-fonts/releases/latest/download/NerdFontsSymbolsOnly.zip> and unzip it. On Windows, select the `.ttf` files, right-click and choose *Install* (or *Install for all users*). On macOS, open the `.ttf` files and click *Install Font*. On Linux, copy them into `~/.local/share/fonts` and run `fc-cache -fv`.

### 2. If you still see boxes

Only if the icons still do not show in a new window, add the symbols font as a **fallback after your current font**, without removing it. Terminals that accept a list of fonts can do it:

| Terminal | Where |
|---|---|
| Windows Terminal | Settings → your profile (or *Defaults*) → Appearance → Font face: `Your Font, Symbols Nerd Font` |
| VS Code (integrated terminal) | Setting `terminal.integrated.fontFamily`, for example `"Your Font, Symbols Nerd Font"` |

If your terminal has no font list (macOS Terminal), do not change your font: use plain text with `STATUSLINE_ICONS=0`, or use the alternative below knowing that it replaces your font.

### Alternative: a complete Nerd Font as your terminal font

A complete Nerd Font is a regular font with the icons patched in, so using it **changes the font you see**. Pick one from the [download page](https://www.nerdfonts.com/font-downloads), where every font has a live preview (use the **v3.x** release; `CaskaydiaCove Nerd Font` is Cascadia Code with the icons; use its regular variant, because the `Mono` variant makes the icons smaller), install it, then select it in your terminal's font menu (macOS Terminal: Settings → Profiles → Text → Font; iTerm2: Settings → Profiles → Text → Font; GNOME Terminal: Preferences → your profile → Text → Custom font) and restart the terminal.

```bash
brew install --cask font-caskaydia-cove-nerd-font   # macOS; every Nerd Font has its own cask
```

### Ghostty: full-size icons with your own font

A `Mono` Nerd Font (for example `FiraCode Nerd Font Mono`) squeezes every icon into one cell, so the icons look smaller than the text. Ghostty can take only the icons from another font and keep yours for everything else, with `font-codepoint-map`. The status line's icons are Octicons, in the range `U+F400`-`U+F533`. Install a regular (not `Mono`) Nerd Font, then add one line to your Ghostty config:

```text
font-codepoint-map = U+F400-U+F533=CaskaydiaCove Nerd Font
```

Your `font-family` stays as it is. Reload the config (Cmd+Shift+, on macOS) or open a new window. `ghostty +list-fonts` shows the font names you can use.

### Check it

```bash
python3 -c "print('\uf412 \uf413 \uf418 \uf4bc \uf4e3 \uf439 \uf4a0 \uf469')"
```

You should see a tag, a folder, a branch, a chip, an hourglass, a card, a task list and a pulse. If you see boxes or question marks, the symbols font is not being used in that terminal: install it (step 1), open a new window, then try step 2, or use `STATUSLINE_ICONS=0`.

If the icons render but look slightly off, or the end of line 1 is clipped, see [Troubleshooting](#troubleshooting).

## Configuration

All settings are **optional environment variables**. A value that is not a number (for example `STATUSLINE_MARGIN=abc`) is ignored and the default is used. Put them in front of the command in `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "STATUSLINE_ICONS=0 STATUSLINE_GIT_USER=0 python3 ~/.claude/statusline.py",
    "refreshInterval": 30
  }
}
```

| Variable | Default | Effect |
|---|---|---|
| `STATUSLINE_ICONS` | `1` (on) | `0` replaces every Nerd Font icon with plain text (`→` for reset times, `⚡` for fast mode). Use it if your terminal has no Nerd Font. |
| `STATUSLINE_GIT_USER` | `1` (on) | `0` hides the git user on line 2. When off, the script does not even call git for it. The user is only ever shown inside a git repository. |
| `STATUSLINE_SPEED` | `1` (on) | `0` hides the approximate speed of the last response (`~N tok/s`) and the script does not read the transcript. |
| `STATUSLINE_TOKENS` | `0` (off) | `1` adds a third line with the last API call's tokens: `I` input, `O` output, `R` cache read, `W` cache write. |
| `STATUSLINE_FLEX` | `1` (on) | `0` stops pushing the usage group, session cost and context to the right edge of line 1; they follow the left group. Flex also falls back to this by itself when the terminal width is unknown or too small. |
| `STATUSLINE_MARGIN` | `8` | Cells left free on the right of the right group in flex mode. Claude Code reserves part of the row and shows its own notices there. **Raise it** (for example `12`) if the end of line 1 appears cut with `…`. |
| `STATUSLINE_ICON_CELLS` | `1` | Set to `2` if your terminal draws each icon two cells wide. It only affects the alignment calculation in flex mode. |

Related Claude Code settings (these live in the `statusLine` block, not in this script): `refreshInterval` (seconds between refreshes) and `padding` (extra horizontal spacing). See the [Claude Code status line docs](https://code.claude.com/docs/en/statusline).

Flex mode reads `COLUMNS`, which Claude Code sets to the real terminal width before it runs the script.

### Changing bar sizes, icons and colors

These are constants at the top of `statusline.py`, meant to be edited directly:

| Constant | What it controls |
|---|---|
| `BAR_5H`, `BAR_WIDTH` | Width in cells of the 5-hour bar (default 10) and of the 7d and context bars (default 6). The `Budget` bar is `BAR_5H` wide. The usage and context bars grow by one cell when that keeps the percentage inside them centered. |
| `GIT_TIMEOUT`, `MAX_COLUMNS` | Seconds each git call may take (1) and the widest terminal the layout will assume (1000). |
| `ICON` / `TEXT` | The icon (Nerd Font code point) and the plain-text replacement used for each field. |
| `TONE` | Text colors. Plain ANSI numbers follow your terminal theme, `38;5;N` values are fixed 256-color. |
| `BG` | Background colors of the filled part of a bar. |
| `level_tone(p, warn, crit)` | The thresholds: green below `warn` (60), amber from `warn`, red from `crit` (80). Text and bars use the same two points. |

## Colors and thresholds

| State | Color | Applies to |
|---|---|---|
| healthy | green | percentages and bars below the warning level |
| warning | yellow | 60-79%, for both the percentage text and the bars; `/compact`; `Opus`; effort `high`, `xhigh`, `max` |
| critical | red | 80% and above; the red `/compact`; the `Rolling` word and bar turn red while the 5-hour window is critical |
| fast mode | orange | the rocket and the word `fast` |
| empty part of a bar | gray | background |

The green and the yellow are **fixed 256-color values** (`#5fd75f` and `#ffd700`) on purpose: the plain ANSI "yellow" of some themes is actually a lime green and gets confused with healthy green.

## workflow-dev story cost

[workflow-dev](https://github.com/lbecjx/workflow-dev) is a Claude Code plugin that runs a story through init, plan, implement and validate, and records what each step cost in the project. A story usually spans several sessions, and a session can work on more than one story, so the story cost and the session cost are two different numbers. The status line shows both: the story cost on the left, the session cost on the right.

The two tools do not depend on each other. Each works alone, and the status line only reads what workflow-dev leaves in the project; it never writes there.

- **Read:** `.workflow-dev/context/.usage/.index.json`, which workflow-dev 1.33.0 or later rewrites at every checkpoint. The status line understands `schema` `workflow-dev.usage/1` and `workflow-dev.usage/2` (workflow-dev 1.36.0 or later). With no file, another schema, or a file it cannot read, nothing is shown and nothing is reported.

The story cost is shown only for the story you are working on. All three must hold, otherwise nothing is shown:

1. **The project uses workflow-dev:** `.workflow-dev/context/REPO.md` exists, next to the index.
2. **The current branch is for that story:** the story shown is the one in the index whose id appears in the branch name, upper or lower case (`ccdt-0006-story-cost` shows `CCDT-0006`). If several ids appear, the longest one wins.
3. **The story is still open.** The status line looks for a status in `.workflow-dev/context/<ID>.md` (a line such as `### Implementation Status: Done`) and, only if the project also uses [local-backlog](https://github.com/lbecjx/local-backlog) (`local-backlog/.backlog-config.json` exists), in the `Status` row of `local-backlog/<ID>-*.md`. The first known status wins. `Done`, `Won't Do`, `Closed`, `Cancelled`, `Merged` and `Abandoned` (and in Spanish `Hecha`, `Terminada`, `Cerrada`, `Descartada`) hide the story; `In Progress`, `Started`, `WIP`, `Open` and `Blocked` (and `En progreso`, `En curso`, `Abierta`) keep it. Case, spaces, Markdown marks and a note after the value (`Done (all ACs)`) do not matter. A value that is neither says nothing, so the next file decides, and with no known status at all the story counts as open.

## Providers

What you see depends on what Claude Code sends, which depends on how you authenticate:

| How you use Claude Code | Usage bars | Cost |
|---|---|---|
| Claude **Pro / Max** subscription | `Rolling` and `Weekly` windows (after the first response of a session) | shown as `eq` |
| **Amazon Bedrock**, direct API | none: Claude Code sends no subscription limits, so the usage group is hidden | shown if Claude Code computes it |
| Behind a **Claude apps gateway** with a spend limit | a `spend` bar (needs Claude Code 2.1.251 or later) | shown as `eq` |

Nothing in the status line knows your AWS or API balance: Claude Code does not expose it. For a real spending limit on Bedrock use your cloud provider's budget alerts.

## Try it without a live session

`examples/demo.py` prints a sample payload with the fields Claude Code sends:

```bash
python3 examples/demo.py | python3 statusline.py
python3 examples/demo.py --critical | python3 statusline.py       # 5h window almost exhausted
python3 examples/demo.py --opus --fast | python3 statusline.py
python3 examples/demo.py --bedrock | python3 statusline.py        # no limits, long model id
python3 examples/demo.py --spend | python3 statusline.py          # gateway spend limit
python3 examples/demo.py --story | python3 statusline.py          # workflow-dev story cost (creates a temp git repo)
```

Add `STATUSLINE_ICONS=0` in front to see the plain-text version, and `COLUMNS=140` to see the right-aligned layout (your shell may not export `COLUMNS` on its own).

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Boxes or `?` instead of icons | The terminal has no font with the Nerd Font icons. See [Icons and Nerd Fonts](#icons-and-nerd-fonts), or set `STATUSLINE_ICONS=0`. |
| The end of line 1 is cut with `…` | Claude Code reserves space on the right. Raise `STATUSLINE_MARGIN`. |
| Icons overlap the text | Your terminal draws icons wider than one cell. Use the `Mono` variant of your Nerd Font (for a symbols font, `SymbolsNerdFontMono-Regular.ttf` in the downloaded zip), or set `STATUSLINE_ICON_CELLS=2`. |
| Icons look tiny | You are using a `Mono` variant, which shrinks every icon to fit one cell. Switch to the regular variant of the same Nerd Font (for example `CaskaydiaCove Nerd Font` instead of `CaskaydiaCove Nerd Font Mono`). |
| No `Rolling` / `Weekly` bars | They only exist with a Pro / Max subscription, and only after the first response of a session. With Bedrock or an API key they never exist. |
| No branch and no user | You are not inside a git repository, or `git` is not installed. This is intentional. |
| No session name | None has been set yet. Use `claude --name "..."` or `/rename`. |
| Nothing shows up at all | Run `python3 examples/demo.py \| python3 statusline.py`. If that prints, the script is fine and the problem is the `statusLine` block in `settings.json`. |

## Versioning

Releases follow [Semantic Versioning](https://semver.org). While the major version is 0, the output and the configuration may still change between minor versions. Every change is listed in the [CHANGELOG](CHANGELOG.md).

Check which version you have installed:

```bash
python3 ~/.claude/statusline.py --version
```

The installation prompt downloads the script from the latest release. To install a specific release, use its tag in the download URL instead, for example `https://github.com/lbecjx/claude-code-dashboard-term/releases/download/v0.2.0/statusline.py`. Each release is published at <https://github.com/lbecjx/claude-code-dashboard-term/releases> with its notes from the CHANGELOG and `statusline.py` and `demo.py` attached. Pushing a `v*` tag creates it, after checking that the tag, the `__version__` in the script and the newest CHANGELOG entry agree.

## Issues and contributions

Found a bug, a terminal where it looks wrong, or a provider whose data it does not handle? Open an issue at <https://github.com/lbecjx/claude-code-dashboard-term/issues>, ideally with the output of `python3 examples/demo.py | python3 statusline.py` and your terminal and font.

## Uninstall

1. Remove the `statusLine` block from `~/.claude/settings.json` (or restore the backup you made).
2. Delete `~/.claude/statusline.py` (or restore your previous one).

## Privacy and safety

- The script reads the JSON on its standard input; for the speed, the last 256 KiB of the session transcript file that Claude Code names in `transcript_path` (read-only; set `STATUSLINE_SPEED=0` to skip it); and, inside a git repository that uses workflow-dev, its cost index `.workflow-dev/context/.usage/.index.json` and the status line of the current story in `.workflow-dev/context/<ID>.md` or `local-backlog/<ID>-*.md` (read-only, at most 1 MiB each).
- It makes no network connections and writes no files: its only output is standard output.
- It runs `git` locally, with a one-second timeout each, to learn whether you are in a repository and where its root is (`git rev-parse --show-toplevel`), the branch (`git branch --show-current`) and the user (`git config user.name`). Set `STATUSLINE_GIT_USER=0` to skip the last one.
- Whatever Claude Code sends, a missing, wrong-typed or absurd value is ignored and the script never prints a traceback. Text that comes from the payload or from git (names, folders, branches) has control characters, line breaks and terminal escape sequences removed before it is printed.
- Screenshots of the status line can show your git user name and branch. Turn the user off before sharing one.

As with any script you run on every refresh, read it before installing it. It is a single short file.

## Attribution and licenses

- **Icons.** [Octicons](https://github.com/primer/octicons) by GitHub, licensed MIT (Copyright GitHub, Inc.). This project does **not** bundle or redistribute them: the script prints Unicode code points, and your terminal draws them from the Nerd Font you installed. The code points come from the [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) glyph table (v3.5.1).
- **Nerd Fonts.** [Nerd Fonts](https://www.nerdfonts.com) patches developer fonts with icon sets. Its patched fonts are under the SIL Open Font License 1.1 and its scripts under MIT; each icon set it includes keeps its own license. If you redistribute a Nerd Font, follow the licenses that ship with it.
- **Claude Code** is a product of Anthropic. This project is an independent community script, and is not affiliated with, endorsed by or supported by Anthropic or GitHub.
- The input format is the one documented in the [Claude Code status line docs](https://code.claude.com/docs/en/statusline).

## License

Copyright (C) 2026 lbecjx

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. See [LICENSE](LICENSE) for the full text.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
