# Changelog

All notable changes to this project are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the major version is 0, output and
configuration may still change between minor versions.

## [0.2.0] - 2026-10-01

### Added
- `python3 statusline.py --version` prints the installed version.
- Model names given as Vertex ids (`claude-opus-4-5@20251101`) or with a `[1m]` suffix are shortened like Bedrock ids.
- GitHub Actions: a CI workflow that compiles and smoke-tests the script, and a release workflow that publishes a GitHub release when a `v*` tag is pushed.

### Changed
- Percentage text and bars change color at the same points: yellow from 60%, red from 80%. The text used to turn yellow at 50%.
- From 80% of the context window the hint is a red `/compact`. `/clear` is no longer suggested.
- A percentage is rounded once, and the rounded value drives the text, the color and the hints.
- The estimated cost is hidden until it reaches one cent.
- Text taken from the payload or from git has control characters and line breaks removed before it is printed.
- Terminal width is counted per character: East Asian wide characters count as two cells.
- `STATUSLINE_MARGIN` has a minimum of 0 and `COLUMNS` a maximum of 1000.
- The icons in the source and in the README are written as `\uXXXX` escapes.

### Removed
- The `(~2x)` note shown next to the cost with Opus: Claude Code does not report a price ratio.

### Fixed
- A non-numeric `STATUSLINE_MARGIN` or `STATUSLINE_ICON_CELLS` is ignored and the default is used.
- Missing, wrong-typed or out-of-range fields in the payload are ignored, and the rest of the line is still printed.
- Branch and git user are not shown when the payload names no directory.
- `GIT_DIR` and related environment variables no longer redirect the git lookups.
- Token counts just below one million show as `1M` instead of `1000K`.
- A leading byte order mark and a closed output pipe are handled without errors.

## [0.1.0] - 2026-10-01

### Added
- Status line for Claude Code showing model, effort, usage bars (`5h`, `7d`, `spend`), estimated cost and context window.
- Second line with session name, folder, and git branch and user.
- Six `STATUSLINE_*` environment variables to switch icons, git user, token line, right alignment, margin and icon width.
- `examples/demo.py`, a sample payload generator for trying the script without a live session.
- README with a copy-paste installation prompt for Claude Code, manual installation and Nerd Font setup.
- GPL-3.0-or-later license.

[0.2.0]: https://github.com/lbecjx/claude-code-dashboard-term/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lbecjx/claude-code-dashboard-term/releases/tag/v0.1.0
