# Copyright 2024 Google LLC
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

import base64
import contextlib
import io
import json
import os
import shutil
import tempfile
from typing import Any, AnyStr, BinaryIO, ContextManager, Iterator, Optional, Tuple
import unittest
from unittest.mock import patch
import main
import data_references


class _TempFile(object):
  """Represents a tempfile for tests.

  Creation of this class is internal. Using its public methods is OK.

  This class implements the `os.PathLike` interface (specifically,
  `os.PathLike[str]`). This means, in Python 3, it can be directly passed
  to e.g. `os.path.join()`.
  """

  def __init__(self, path: str) -> None:
    """Private: use _create instead."""
    self._path = path

  @classmethod
  def _create(
      cls,
      base_path: str,
      file_path: Optional[str],
      content: AnyStr,
      mode: str,
      encoding: str,
      errors: str,
  ) -> Tuple['_TempFile', str]:
    """Module-private: create a tempfile instance."""
    if file_path:
      cleanup_path = os.path.join(base_path, _get_first_part(file_path))
      path = os.path.join(base_path, file_path)
      os.makedirs(os.path.dirname(path), exist_ok=True)
      # The file may already exist, in which case, ensure it's writable so that
      # it can be truncated.
      if os.path.exists(path) and not os.access(path, os.W_OK):
        stat_info = os.stat(path)
        os.chmod(path, stat_info.st_mode | stat.S_IWUSR)
    else:
      os.makedirs(base_path, exist_ok=True)
      fd, path = tempfile.mkstemp(dir=str(base_path))
      os.close(fd)
      cleanup_path = path

    tf = cls(path)

    if content:
      if isinstance(content, str):
        tf.write_text(content, mode=mode, encoding=encoding, errors=errors)
      else:
        tf.write_bytes(content, mode)

    else:
      tf.write_bytes(b'')

    return tf, cleanup_path

  @property
  def full_path(self) -> str:
    """Returns the path, as a string, for the file.

    TIP: Instead of e.g. `os.path.join(temp_file.full_path)`, you can simply
    do `os.path.join(temp_file)` because `__fspath__()` is implemented.
    """
    return self._path

  def __fspath__(self) -> str:
    """See os.PathLike."""
    return self.full_path

  def write_bytes(self, data: bytes, mode: str = 'wb') -> None:
    """Write bytes to the file.

    Args:
      data: bytes to write.
      mode: Mode to open the file for writing. The "b" flag is implicit if not
        already present. It must not have the "t" flag.
    """
    with self.open_bytes(mode) as fp:
      fp.write(data)

  def open_bytes(self, mode: str = 'rb') -> ContextManager[BinaryIO]:
    """Return a context manager for opening the file in binary mode.

    Args:
      mode: The mode to open the file in. The "b" mode is implicit if not
        already present. It must not have the "t" flag.

    Returns:
      Context manager that yields an open file.

    Raises:
      ValueError: if invalid inputs are provided.
    """
    if 't' in mode:
      raise ValueError(
          'Invalid mode {!r}: "t" flag not allowed when opening '
          'file in binary mode'.format(mode)
      )
    if 'b' not in mode:
      mode += 'b'
    cm = self._open(mode, encoding=None, errors=None)
    return cm

  @contextlib.contextmanager
  def _open(
      self,
      mode: str,
      encoding: Optional[str] = 'utf8',
      errors: Optional[str] = 'strict',
  ) -> Iterator[Any]:
    with io.open(
        self.full_path, mode=mode, encoding=encoding, errors=errors
    ) as fp:
      yield fp


class _TempDir(object):
  """Represents a temporary directory for tests.

  Creation of this class is internal. Using its public methods is OK.

  This class implements the `os.PathLike` interface (specifically,
  `os.PathLike[str]`). This means, in Python 3, it can be directly passed
  to e.g. `os.path.join()`.
  """

  def __init__(self, path: str) -> None:
    """Module-private: do not instantiate outside module."""
    self._path = path

  @property
  def full_path(self) -> str:
    """Returns the path, as a string, for the directory.

    TIP: Instead of e.g. `os.path.join(temp_dir.full_path)`, you can simply
    do `os.path.join(temp_dir)` because `__fspath__()` is implemented.
    """
    return self._path

  def create_file(
      self,
      file_path: Optional[str] = None,
      content: Optional[AnyStr] = None,
      mode: str = 'w',
      encoding: str = 'utf8',
      errors: str = 'strict',
  ) -> '_TempFile':
    """Create a file in the directory.

    NOTE: If the file already exists, it will be made writable and overwritten.

    Args:
      file_path: Optional file path for the temp file. If not given, a unique
        file name will be generated and used. Slashes are allowed in the name;
        any missing intermediate directories will be created. NOTE: This path is
        the path that will be cleaned up, including any directories in the path,
        e.g., 'foo/bar/baz.txt' will `rm -r foo`
      content: Optional string or bytes to initially write to the file. If not
        specified, then an empty file is created.
      mode: Mode string to use when writing content. Only used if `content` is
        non-empty.
      encoding: Encoding to use when writing string content. Only used if
        `content` is text.
      errors: How to handle text to bytes encoding errors. Only used if
        `content` is text.

    Returns:
      A _TempFile representing the created file.
    """
    tf, _ = _TempFile._create(
        self._path, file_path, content, mode, encoding, errors
    )
    return tf


class TestMain(unittest.TestCase):

  def testConfig_retrieval_successful_with_correct_file(self):
    file_dict = {
        'use_proto_plus': True,
        'developer_token': 'zZzZzZz',
        'client_id': '123456789',
        'client_secret': 'ClIeNt_sEcReT',
        'access_token': 'z-z-Z-Z',
        'refresh_token': 'Y-y-Y-y',
        'login_customer_id': '12345',
        'customer_id_inclusion_list': '654321',
        'spreadsheet_id': 'SheetId123',
    }
    out_dir = self.create_tempdir('tmp_test')
    json_string = json.dumps(file_dict).encode('utf-8')
    out_file = out_dir.create_file('output_correct_file.yaml', json_string)

    result = main.retrieve_config(out_file)
    expected = data_references.ConfigFile(
        True,
        'zZzZzZz',
        '123456789',
        'ClIeNt_sEcReT',
        'z-z-Z-Z',
        'Y-y-Y-y',
        '12345',
        '654321',
        'SheetId123',
    )

    self.assertEqual(result, expected)

  def testConfig_retrieval_fails_with_incorrect_file(self):
    file_dict = {
        'use_proto_plus': True,
        'developer_token_wrong': 'zZzZzZz',
        'client_id_wrong': '123456789',
        'refresh_token': 'Y-y-Y-y',
        'login_customer_id': '12345',
        'customer_id_inclusion_list': '654321',
        'spreadsheet_id': 'SheetId123',
    }

    out_dir = self.create_tempdir('tmp_test')
    json_string = json.dumps(file_dict).encode('utf-8')
    out_file = out_dir.create_file('output_wrong_file.yaml', json_string)

    self.assertRaises(TypeError, main.retrieve_config, out_file)

  @patch('pubsub.PubSub.refresh_spreadsheet')
  def test_pmax_trigger_to_call_refresh_spreadsheet_for_refresh_cloud_event(
      self, mock_refresh_spreadsheet
  ):
    encoded_refresh_data = base64.b64encode('REFRESH'.encode('utf-8'))
    mock_cloud_event = type(
        'mock_CloudEvent',
        (object,),
        {'data': {'message': {'data': encoded_refresh_data}}},
    )

    main.pmax_trigger(mock_cloud_event)

    mock_refresh_spreadsheet.assert_called()

  @patch('pubsub.PubSub.create_api_operations')
  def test_pmax_trigger_to_call_create_api_operations_for_upload_cloud_event(
      self, mock_create_api_operations
  ):
    encoded_refresh_data = base64.b64encode('UPLOAD'.encode('utf-8'))
    mock_cloud_event = type(
        'mock_CloudEvent',
        (object,),
        {'data': {'message': {'data': encoded_refresh_data}}},
    )

    main.pmax_trigger(mock_cloud_event)

    mock_create_api_operations.assert_called()

  @patch('pubsub.PubSub.refresh_spreadsheet')
  @patch('pubsub.PubSub.create_api_operations')
  @patch('pubsub.PubSub.refresh_customer_id_list')
  @patch('pubsub.PubSub.refresh_campaign_list')
  @patch('pubsub.PubSub.refresh_asset_group_list')
  @patch('pubsub.PubSub.refresh_assets_list')
  @patch('pubsub.PubSub.refresh_sitelinks_list')
  def test_pmax_trigger_to_call_nothing_for_random_cloud_event(
      self,
      mock_refresh_spreadsheet,
      mock_create_api_operations,
      mock_refresh_customer_id_list,
      mock_refresh_campaign_list,
      mock_refresh_asset_group_list,
      mock_refresh_assets_list,
      mock_refresh_sitelinks_list,
  ):
    encoded_refresh_data = base64.b64encode('UPLOADDDD'.encode('utf-8'))
    mock_cloud_event = type(
        'mock_CloudEvent',
        (object,),
        {'data': {'message': {'data': encoded_refresh_data}}},
    )

    main.pmax_trigger(mock_cloud_event)

    mock_create_api_operations.assert_not_called()
    mock_refresh_spreadsheet.assert_not_called()
    mock_refresh_customer_id_list.assert_not_called()
    mock_refresh_campaign_list.assert_not_called()
    mock_refresh_asset_group_list.assert_not_called()
    mock_refresh_assets_list.assert_not_called()
    mock_refresh_sitelinks_list.assert_not_called()

  def create_tempdir(self, name: str) -> _TempDir:
    """Create a temporary directory specific to the test.

    NOTE: The directory and its contents will be recursively cleared before
    creation. This ensures that there is no pre-existing state.

    This creates a named directory on disk that is isolated to this test, and
    will be properly cleaned up by the test. This avoids several pitfalls of
    # absl:google3-begin(Comment for google3-users)
    (see go/python-tips/032#use-create-tempfile)
    # absl:google3-end
    creating temporary directories for test purposes, as well as makes it easier
    to setup directories and verify their contents. For example::

        def test_foo(self):
          out_dir = self.create_tempdir()
          out_log = out_dir.create_file('output.log')
          expected_outputs = [
              os.path.join(out_dir, 'data-0.txt'),
              os.path.join(out_dir, 'data-1.txt'),
          ]
          code_under_test(out_dir)
          self.assertTrue(os.path.exists(expected_paths[0]))
          self.assertTrue(os.path.exists(expected_paths[1]))
          self.assertEqual('foo', out_log.read_text())

    See also: :meth:`create_tempfile` for creating temporary files.

    Args:
      name: Optional name of the directory. If not given, a unique name will be
        generated and used.
      cleanup: Optional cleanup policy on when/if to remove the directory (and
        all its contents) at the end of the test. If None, then uses
        :attr:`tempfile_cleanup`.

    Returns:
      A _TempDir representing the created directory; see _TempDir class docs
      for usage.
    """
    test_path = os.getcwd()
    path = os.path.join(test_path, name)
    cleanup_path = os.path.join(test_path, _get_first_part(name))

    _rmtree_ignore_errors(cleanup_path)
    os.makedirs(path, exist_ok=True)

    self.addCleanup(_rmtree_ignore_errors, path)

    return _TempDir(path)


def _get_first_part(path: str) -> str:
  parts = path.split(os.sep, 1)
  return parts[0]


def _rmtree_ignore_errors(path: str) -> None:
  if os.path.isfile(path):
    try:
      os.unlink(path)
    except OSError:
      pass
  else:
    shutil.rmtree(path, ignore_errors=True)
