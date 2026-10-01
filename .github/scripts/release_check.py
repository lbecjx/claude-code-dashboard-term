#!/usr/bin/env python3
# claude-code-dashboard-term — a status line for Claude Code: model, usage limits, cost, context and git
# https://github.com/lbecjx/claude-code-dashboard-term
# Copyright (C) 2026  lbecjx
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See LICENSE for the full text.
"""Check that the script version, CHANGELOG.md and (optionally) a git tag agree, and extract release notes.

    python3 .github/scripts/release_check.py                          # script version vs CHANGELOG
    python3 .github/scripts/release_check.py v0.2.0                   # ... and the tag
    python3 .github/scripts/release_check.py v0.2.0 --notes notes.md  # ... and write that version's notes

Exit status 0 when everything agrees, 1 otherwise. Used by the CI and release workflows.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SEMVER = re.compile(r"\d+\.\d+\.\d+")


def fail(message):
    print(f"::error::{message}")   # shown as an annotation in GitHub Actions, and readable in a terminal
    sys.exit(1)


def script_version():
    source = (ROOT / "statusline.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__ = "([^"]+)"', source, re.M)
    if not match:
        fail("statusline.py does not define __version__")
    if not SEMVER.fullmatch(match.group(1)):
        fail(f"__version__ {match.group(1)!r} is not MAJOR.MINOR.PATCH")
    return match.group(1)


def changelog_releases():
    """[(version, notes)] for every released section of CHANGELOG.md, newest first. [Unreleased] is skipped."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## \[([^\]]+)\][^\n]*\n", text)   # [preamble, version, body, version, body, ...]
    releases = []
    for version, body in zip(parts[1::2], parts[2::2]):
        if SEMVER.fullmatch(version):
            body = re.split(r"(?m)^\[[^\]]+\]: ", body)[0]   # drop the link references at the end of the file
            releases.append((version, body.strip()))
    return releases


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tag", nargs="?", help="git tag to check, for example v0.2.0")
    parser.add_argument("--notes", metavar="FILE", help="write the CHANGELOG notes of this version to FILE")
    args = parser.parse_args()

    version = script_version()
    releases = changelog_releases()
    if not releases:
        fail("CHANGELOG.md has no released version section like '## [0.1.0] - 2026-01-01'")
    top_version, notes = releases[0]
    if top_version != version:
        fail(f"CHANGELOG.md's newest version is {top_version} but statusline.py says {version}")
    if args.tag and args.tag != f"v{version}":
        fail(f"tag {args.tag} does not match version {version} (expected v{version})")
    if not re.search(r"(?m)^- ", notes):
        fail(f"the CHANGELOG.md section for {version} has no bullet points")
    if args.notes:
        pathlib.Path(args.notes).write_text(notes + "\n", encoding="utf-8")
    print(f"OK: version {version}" + (f", tag {args.tag}" if args.tag else "") + ", CHANGELOG.md in agreement")


if __name__ == "__main__":
    main()
