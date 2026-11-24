# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Pull request checks that only look at the lines a change adds.

Usage (from the repository root):
  python .github/scripts/ci_checks.py format --base origin/main
  python .github/scripts/ci_checks.py guards --base origin/main

"format" runs pyink on the changed lines of changed Python files, so old code
is not reformatted as a side effect. "guards" blocks local configuration files
and new USER_ENTERED Sheet writes (formula injection, CWE-1236).
"""

import argparse
import collections
from collections.abc import Mapping, Sequence
import dataclasses
import fnmatch
import re
import subprocess
import sys

_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

# Files that hold real settings or secrets and must never be committed.
_FORBIDDEN_PATH_PATTERNS = (
    "terraform/configuration-input.tfvars",
    "*config.yaml",
    "*.tfstate",
    "*.tfstate.*",
    "*.terraform/*",
)

# Only trusted, hardcoded formulas may use USER_ENTERED; all other Sheet
# writes must use RAW so that text from Google Ads is never run as a formula.
_USER_ENTERED = "USER_ENTERED"

_FORBIDDEN_PATHS_MESSAGE = (
    "These files hold real settings or secrets and must not be committed:"
)
_USER_ENTERED_MESSAGE = (
    "New USER_ENTERED Sheet writes found. Use RAW for any value that comes"
    " from Google Ads or users (formula injection, CWE-1236):"
)


@dataclasses.dataclass(frozen=True)
class AddedLine:
  """A line that a change adds to a file.

  Attributes:
    path: Repository-relative path of the file.
    line_number: 1-based line number in the new version of the file.
    text: The added line, without the leading "+".
  """

  path: str
  line_number: int
  text: str


def parse_added_lines(diff_text: str) -> Sequence[AddedLine]:
  """Extracts the added lines from a unified diff made with -U0.

  Args:
    diff_text: Output of "git diff -U0".

  Returns:
    Every added line, in diff order. Lines of deleted files are skipped.
  """
  added_lines = []
  path = None
  line_number = 0
  for raw_line in diff_text.splitlines():
    if raw_line.startswith("+++ "):
      target = raw_line[4:]
      path = target[2:] if target.startswith("b/") else None
      continue
    if raw_line.startswith("--- "):
      continue
    header = _HUNK_HEADER.match(raw_line)
    if header:
      line_number = int(header.group(1))
      continue
    if path is not None and raw_line.startswith("+"):
      added_lines.append(AddedLine(path, line_number, raw_line[1:]))
      line_number += 1
  return added_lines


def to_line_ranges(
    added_lines: Sequence[AddedLine],
) -> Mapping[str, Sequence[tuple[int, int]]]:
  """Groups added lines into inclusive line ranges per file.

  Args:
    added_lines: Added lines, as returned by parse_added_lines.

  Returns:
    A mapping from file path to sorted (start, end) ranges of added lines.
  """
  numbers_by_path = collections.defaultdict(list)
  for line in added_lines:
    numbers_by_path[line.path].append(line.line_number)
  ranges_by_path = {}
  for path, numbers in numbers_by_path.items():
    ranges = []
    for number in sorted(numbers):
      if ranges and number == ranges[-1][1] + 1:
        ranges[-1] = (ranges[-1][0], number)
      else:
        ranges.append((number, number))
    ranges_by_path[path] = ranges
  return ranges_by_path


def find_forbidden_paths(changed_paths: Sequence[str]) -> Sequence[str]:
  """Returns the changed paths that must never be committed.

  Args:
    changed_paths: Repository-relative paths that a change adds or modifies.
  """
  return [
      path
      for path in changed_paths
      if any(
          fnmatch.fnmatch(path, pattern) for pattern in _FORBIDDEN_PATH_PATTERNS
      )
  ]


def find_new_user_entered_writes(
    added_lines: Sequence[AddedLine],
) -> Sequence[AddedLine]:
  """Returns added USER_ENTERED lines in Cloud Function code (not tests).

  Args:
    added_lines: Added lines, as returned by parse_added_lines.
  """
  return [
      line
      for line in added_lines
      if line.path.startswith("functions/")
      and not line.path.startswith("functions/test/")
      and line.path.endswith(".py")
      and _USER_ENTERED in line.text
  ]


def _git(*args: str) -> str:
  """Runs a git command and returns its standard output."""
  return subprocess.run(
      ["git", *args], check=True, capture_output=True, text=True
  ).stdout


def _check_format(base: str, pyink_command: str) -> int:
  """Runs pyink on the changed lines of changed Python files.

  Args:
    base: Git revision to compare against.
    pyink_command: Name or path of the pyink executable.

  Returns:
    0 if the changed lines are formatted, 1 otherwise.
  """
  diff_text = _git(
      "diff",
      "-U0",
      "--no-color",
      "--diff-filter=AM",
      f"{base}...HEAD",
      "--",
      "*.py",
  )
  ranges_by_path = to_line_ranges(parse_added_lines(diff_text))
  failed = False
  for path, ranges in sorted(ranges_by_path.items()):
    range_args = [f"--line-ranges={start}-{end}" for start, end in ranges]
    result = subprocess.run(
        [pyink_command, "--check", "--diff", *range_args, path], check=False
    )
    failed = failed or result.returncode != 0
  if failed:
    print("Run pyink on the lines you changed (settings in pyproject.toml).")
  return 1 if failed else 0


def _report(problems: Mapping[str, Sequence[str]]) -> int:
  """Prints guard problems and returns the exit code."""
  for title, items in problems.items():
    if items:
      print(f"::error::{title}")
      for item in items:
        print(f"  {item}")
  return 1 if any(problems.values()) else 0


def _check_guards(base: str) -> int:
  """Blocks local configuration files and new USER_ENTERED writes.

  Args:
    base: Git revision to compare against.

  Returns:
    0 if no guard is hit, 1 otherwise.
  """
  changed_paths = _git(
      "diff", "--name-only", "--diff-filter=AMR", f"{base}...HEAD"
  ).splitlines()
  diff_text = _git("diff", "-U0", "--no-color", f"{base}...HEAD")
  new_writes = find_new_user_entered_writes(parse_added_lines(diff_text))
  return _report(
      {
          _FORBIDDEN_PATHS_MESSAGE: find_forbidden_paths(changed_paths),
          _USER_ENTERED_MESSAGE: [
              f"{line.path}:{line.line_number}: {line.text.strip()}"
              for line in new_writes
          ],
      }
  )


def main(argv: Sequence[str]) -> int:
  """Parses the command line and runs one check.

  Args:
    argv: Command-line arguments, without the program name.

  Returns:
    The process exit code.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("check", choices=("format", "guards"))
  parser.add_argument(
      "--base", default="origin/main", help="Git revision to compare against."
  )
  parser.add_argument("--pyink", default="pyink", help="pyink executable.")
  args = parser.parse_args(argv)
  if args.check == "format":
    return _check_format(args.base, args.pyink)
  return _check_guards(args.base)


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
