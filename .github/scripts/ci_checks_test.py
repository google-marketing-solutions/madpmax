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
"""Tests for ci_checks."""

import unittest

import ci_checks

_DIFF = """\
diff --git a/functions/sheet_api.py b/functions/sheet_api.py
index 1111111..2222222 100644
--- a/functions/sheet_api.py
+++ b/functions/sheet_api.py
@@ -10 +10 @@ class SheetsService:
-          valueInputOption="RAW",
+          valueInputOption="USER_ENTERED",
@@ -20,0 +21,2 @@ class SheetsService:
+    first = 1
+    second = 2
diff --git a/functions/test/test_sheet_api.py b/functions/test/test_sheet_api.py
index 3333333..4444444 100644
--- a/functions/test/test_sheet_api.py
+++ b/functions/test/test_sheet_api.py
@@ -5,0 +6 @@
+        valueInputOption="USER_ENTERED",
diff --git a/functions/old.py b/functions/old.py
deleted file mode 100644
index 5555555..0000000
--- a/functions/old.py
+++ /dev/null
@@ -1 +0,0 @@
-gone = True
"""


class ParseAddedLinesTest(unittest.TestCase):

  def test_returns_added_lines_with_new_line_numbers(self):
    lines = ci_checks.parse_added_lines(_DIFF)

    self.assertEqual(
        [(line.path, line.line_number) for line in lines],
        [
            ("functions/sheet_api.py", 10),
            ("functions/sheet_api.py", 21),
            ("functions/sheet_api.py", 22),
            ("functions/test/test_sheet_api.py", 6),
        ],
    )

  def test_skips_deleted_files(self):
    lines = ci_checks.parse_added_lines(_DIFF)

    self.assertNotIn("functions/old.py", {line.path for line in lines})


class ToLineRangesTest(unittest.TestCase):

  def test_merges_consecutive_lines(self):
    ranges = ci_checks.to_line_ranges(ci_checks.parse_added_lines(_DIFF))

    self.assertEqual(ranges["functions/sheet_api.py"], [(10, 10), (21, 22)])


class FindForbiddenPathsTest(unittest.TestCase):

  def test_flags_local_settings_files(self):
    paths = [
        "functions/config.yaml",
        "terraform/configuration-input.tfvars",
        "terraform/terraform.tfstate",
        "terraform/.terraform/providers/x",
    ]

    self.assertEqual(ci_checks.find_forbidden_paths(paths), paths)

  def test_allows_templates_and_code(self):
    paths = ["terraform/config-template.yaml", "functions/main.py"]

    self.assertEqual(ci_checks.find_forbidden_paths(paths), [])


class FindNewUserEnteredWritesTest(unittest.TestCase):

  def test_flags_function_code_but_not_tests(self):
    writes = ci_checks.find_new_user_entered_writes(
        ci_checks.parse_added_lines(_DIFF)
    )

    self.assertEqual(
        [(line.path, line.line_number) for line in writes],
        [("functions/sheet_api.py", 10)],
    )


if __name__ == "__main__":
  unittest.main()
