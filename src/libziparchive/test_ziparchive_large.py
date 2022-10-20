#!/usr/bin/env python3
#
# Copyright (C) 2020 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Unittests for parsing files in zip64 format"""

import os
import subprocess
import tempfile
import unittest
import zipfile
import time

class Zip64Test(unittest.TestCase):
  @staticmethod
  def _WriteFile(path, size_in_kib):
    contents = b'X' * 1024
    with open(path, 'wb') as f:
      for i in range(size_in_kib):
        f.write(contents)

  @staticmethod
  def _AddEntriesToZip(output_zip, entries_dict=None):
    contents = b'X' * 1024
    for name, size in entries_dict.items():
      # Need to pass a ZipInfo with a file_size
      # to .open() so that it adds the Zip64 header
      # on larger files
      info = zipfile.ZipInfo(name)
      info.file_size = size * 1024
      with output_zip.open(info, mode='w') as f:
        for i in range(size):
          f.write(contents)

  def _getEntryNames(self, zip_name):
    cmd = ['ziptool', 'zipinfo', '-1', zip_name]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = proc.communicate()
    self.assertEqual(0, proc.returncode)
    self.assertNotEqual(None, output)
    return output.decode('utf-8').split()

  def _ExtractEntries(self, zip_name):
    with tempfile.TemporaryDirectory() as temp_dir:
      cmd = ['ziptool', 'unzip', '-d', temp_dir, zip_name]
      proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      proc.communicate()
      self.assertEqual(0, proc.returncode)

  def test_entriesSmallerThan2G(self):
    with tempfile.NamedTemporaryFile(suffix='.zip') as zip_path:
      # Add a few entries with each of them smaller than 2GiB. But the entire zip file is larger
      # than 4GiB in size.
      with zipfile.ZipFile(zip_path, 'w', allowZip64=True) as output_zip:
        entry_dict = {'a.txt': 1025 * 1024, 'b.txt': 1025 * 1024, 'c.txt': 1025 * 1024,
                      'd.txt': 1025 * 1024, 'e.txt': 1024}
        self._AddEntriesToZip(output_zip, entry_dict)

      read_names = self._getEntryNames(zip_path.name)
      self.assertEqual(sorted(entry_dict.keys()), sorted(read_names))
      self._ExtractEntries(zip_path.name)


  def test_largeNumberOfEntries(self):
    with tempfile.NamedTemporaryFile(suffix='.zip') as zip_path:
      entry_dict = {}
      # Add 100k entries (more than 65535|UINT16_MAX).
      for num in range(0, 100 * 1024):
        entry_dict[str(num)] = 50

      with zipfile.ZipFile(zip_path, 'w', allowZip64=True) as output_zip:
        self._AddEntriesToZip(output_zip, entry_dict)

      read_names = self._getEntryNames(zip_path.name)
      self.assertEqual(sorted(entry_dict.keys()), sorted(read_names))
      self._ExtractEntries(zip_path.name)


  def test_largeCompressedEntriesSmallerThan4G(self):
    with tempfile.NamedTemporaryFile(suffix='.zip') as zip_path:
      with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED,
                           allowZip64=True) as output_zip:
        # Add entries close to 4GiB in size. Somehow the python library will put the (un)compressed
        # sizes in the extra field. Test if our ziptool should be able to parse it.
        entry_dict = {'e.txt': 4095 * 1024, 'f.txt': 4095 * 1024}
        self._AddEntriesToZip(output_zip, entry_dict)

      read_names = self._getEntryNames(zip_path.name)
      self.assertEqual(sorted(entry_dict.keys()), sorted(read_names))
      self._ExtractEntries(zip_path.name)


  def test_forceDataDescriptor(self):
    with tempfile.NamedTemporaryFile(suffix='.txt') as file_path:
      self._WriteFile(file_path.name, 5000 * 1024)

      with tempfile.NamedTemporaryFile(suffix='.zip') as zip_path:
        with zipfile.ZipFile(zip_path, 'w', allowZip64=True) as output_zip:
          pass
        # The fd option force writes a data descriptor
        cmd = ['zip', '-fd', zip_path.name, file_path.name]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proc.communicate()
        read_names = self._getEntryNames(zip_path.name)
        self.assertEqual([file_path.name[1:]], read_names)
        self._ExtractEntries(zip_path.name)


  def test_largeUncompressedEntriesLargerThan4G(self):
    with tempfile.NamedTemporaryFile(suffix='.zip') as zip_path:
      with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_STORED,
                           allowZip64=True) as output_zip:
        # Add entries close to 4GiB in size. Somehow the python library will put the (un)compressed
        # sizes in the extra field. Test if our ziptool should be able to parse it.
        entry_dict = {'g.txt': 5000 * 1024, 'h.txt': 6000 * 1024}
        self._AddEntriesToZip(output_zip, entry_dict)

      read_names = self._getEntryNames(zip_path.name)
      self.assertEqual(sorted(entry_dict.keys()), sorted(read_names))
      self._ExtractEntries(zip_path.name)


  def test_largeCompressedEntriesLargerThan4G(self):
    with tempfile.NamedTemporaryFile(suffix='.zip') as zip_path:
      with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED,
                           allowZip64=True) as output_zip:
        # Add entries close to 4GiB in size. Somehow the python library will put the (un)compressed
        # sizes in the extra field. Test if our ziptool should be able to parse it.
        entry_dict = {'i.txt': 4096 * 1024, 'j.txt': 7000 * 1024}
        self._AddEntriesToZip(output_zip, entry_dict)

      read_names = self._getEntryNames(zip_path.name)
      self.assertEqual(sorted(entry_dict.keys()), sorted(read_names))
      self._ExtractEntries(zip_path.name)


if __name__ == '__main__':
  unittest.main(verbosity=2)
