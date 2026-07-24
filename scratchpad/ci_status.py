#!/usr/bin/env python3
"""
Pull CircleCI results for a commit/branch straight into the terminal.

Uses `gh api` to resolve the CircleCI build behind a commit's GitHub status, then
the CircleCI v1.1 API (readable unauthenticated for this public repo) to fetch
test results and raw job output.

Written by Claude Sonnet 5 (Claude Code).

Usage:
    dev/ci_status.py summary [--branch BRANCH] [--sha SHA] [--build BUILD_NUM] [--verbose]
    dev/ci_status.py context TEST_NAME [--branch BRANCH] [--sha SHA] [--build BUILD_NUM]
                     [--before N] [--after N]

TEST_NAME matches against "classname::name" (e.g. TestOaiPmhPremium::test_01_no_acc_no_until)
or any substring of it - use whatever uniquely identifies the test.

Examples:
    dev/ci_status.py summary
    dev/ci_status.py summary --branch develop
    dev/ci_status.py summary --build 3345 --verbose
    dev/ci_status.py context TestOaiPmhPremium::test_01_no_acc_no_until --build 3345
"""

import argparse
import json
import re
import subprocess
import sys

import requests

CIRCLECI_CONTEXT = "ci/circleci: build-and-test"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def repo_slug():
    url = sh(["git", "remote", "get-url", "origin"])
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(\.git)?$", url)
    if not m:
        raise SystemExit(f"Could not parse owner/repo from remote url: {url}")
    return m.group(1), m.group(2)


def resolve_sha(branch, sha):
    if sha:
        return sh(["git", "rev-parse", sha])
    if branch:
        try:
            return sh(["git", "rev-parse", f"origin/{branch}"])
        except subprocess.CalledProcessError:
            return sh(["git", "rev-parse", branch])
    try:
        return sh(["git", "rev-parse", "@{u}"])
    except subprocess.CalledProcessError:
        return sh(["git", "rev-parse", "HEAD"])


def resolve_build_num(owner, repo, sha, build):
    if build:
        return str(build)
    out = sh(["gh", "api", f"repos/{owner}/{repo}/commits/{sha}/status"])
    data = json.loads(out)
    for status in data.get("statuses", []):
        if status.get("context") == CIRCLECI_CONTEXT:
            m = re.search(r"/(\d+)$", status["target_url"])
            if m:
                return m.group(1)
    raise SystemExit(f"No CircleCI status found for commit {sha} (context={CIRCLECI_CONTEXT!r})")


def fetch_json(url):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_tests(owner, repo, build_num):
    url = f"https://circleci.com/api/v1.1/project/github/{owner}/{repo}/{build_num}/tests"
    return fetch_json(url).get("tests", [])


def fetch_build(owner, repo, build_num):
    url = f"https://circleci.com/api/v1.1/project/github/{owner}/{repo}/{build_num}"
    return fetch_json(url)


def dedupe_tests(tests):
    seen = {}
    for t in tests:
        key = (t.get("classname"), t.get("name"), t.get("result"))
        seen.setdefault(key, t)
    return list(seen.values())


def test_output_actions(build):
    """Job steps whose action ran a pytest suite (each `index` is a parallel node)."""
    actions = []
    for step in build.get("steps", []):
        for action in step.get("actions", []):
            name = (action.get("name") or "").lower()
            if "unit test" in name or "selenium test" in name:
                actions.append(action)
    return actions


def cmd_summary(args):
    owner, repo = repo_slug()
    sha = resolve_sha(args.branch, args.sha)
    build_num = resolve_build_num(owner, repo, sha, args.build)
    tests = dedupe_tests(fetch_tests(owner, repo, build_num))
    non_success = [t for t in tests if t.get("result") != "success"]

    print(f"build {build_num}  https://circleci.com/gh/{owner}/{repo}/{build_num}")
    print(f"commit {sha}")
    print(f"{len(tests)} tests, {len(non_success)} not passing\n")

    if not non_success:
        print("All green.")
        return

    for t in non_success:
        label = f"{t.get('classname')}::{t.get('name')}"
        print(f"[{t.get('result', '?').upper()}] {label}")
        message = (t.get("message") or "").strip()
        if not message:
            continue
        if args.verbose:
            print("\n".join("    " + l for l in message.splitlines()))
            print()
        else:
            last_line = message.splitlines()[-1] if message else ""
            print(f"    {last_line}")


def cmd_context(args):
    owner, repo = repo_slug()
    sha = resolve_sha(args.branch, args.sha)
    build_num = resolve_build_num(owner, repo, sha, args.build)
    build = fetch_build(owner, repo, build_num)

    found = False
    for action in test_output_actions(build):
        out_url = action.get("output_url")
        idx = action.get("index", 0)
        if not out_url:
            continue
        messages = fetch_json(out_url)
        log = "".join(m.get("message", "") for m in messages)
        log = ANSI_RE.sub("", log)
        if args.test not in log:
            continue

        found = True
        lines = log.splitlines()
        hits = [i for i, l in enumerate(lines) if args.test in l]
        print(f"=== node {idx} ({action.get('name')}) ===")
        for h in hits:
            start = max(0, h - args.before)
            end = min(len(lines), h + args.after + 1)
            for l in lines[start:end]:
                print(l)
            print("...")

    if not found:
        print(f"{args.test!r} not found in any unit/selenium test step output for build {build_num}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--branch", help="branch to check (default: current branch's upstream)")
    common.add_argument("--sha", help="specific commit sha (overrides --branch)")
    common.add_argument("--build", help="specific CircleCI build number (skips GitHub status lookup)")

    p_summary = sub.add_parser("summary", parents=[common], help="list failing/skipped tests for a build")
    p_summary.add_argument("-v", "--verbose", action="store_true", help="print full failure tracebacks")
    p_summary.set_defaults(func=cmd_summary)

    p_context = sub.add_parser("context", parents=[common], help="show test order around a given test in its CI node")
    p_context.add_argument("test", help="test identifier substring, e.g. TestOaiPmhPremium::test_01_no_acc_no_until")
    p_context.add_argument("--before", type=int, default=15, help="lines of context before the match (default 15)")
    p_context.add_argument("--after", type=int, default=3, help="lines of context after the match (default 3)")
    p_context.set_defaults(func=cmd_context)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"command failed: {' '.join(e.cmd)}\n{e.stderr}")
    except requests.HTTPError as e:
        sys.exit(f"HTTP error: {e}")
