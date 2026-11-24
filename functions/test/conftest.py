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
"""Shared pytest fixtures for the Cloud Function unit tests."""

import os
import pathlib
from typing import Iterator

import pytest

# Placeholder values only. The code under test reads "config.yaml" from the
# current working directory, so every test runs in a temporary directory that
# holds this file instead of a real configuration.
_FAKE_CONFIG_YAML = """\
use_proto_plus: true
client_id: "fake-client-id"
client_secret: "fake-client-secret"
refresh_token: "fake-refresh-token"
developer_token: "fake-developer-token"
access_token: "fake-access-token"
login_customer_id: "1234567890"
customer_id_inclusion_list: ""
spreadsheet_id: "fake-spreadsheet-id"
"""


@pytest.fixture(autouse=True)
def fake_config_dir(tmp_path: pathlib.Path) -> Iterator[pathlib.Path]:
  """Runs each test in a temporary directory with a fake config.yaml.

  Args:
    tmp_path: A per-test temporary directory provided by pytest.

  Yields:
    The temporary directory that the test runs in.
  """
  (tmp_path / "config.yaml").write_text(_FAKE_CONFIG_YAML)
  original_dir = os.getcwd()
  os.chdir(tmp_path)
  try:
    yield tmp_path
  finally:
    os.chdir(original_dir)
