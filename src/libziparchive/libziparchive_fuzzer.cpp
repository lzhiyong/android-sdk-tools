// SPDX-License-Identifier: Apache-2.0

#include <stddef.h>
#include <stdint.h>

#include <ziparchive/zip_archive.h>

// See current fuzz coverage here:
// https://android-coverage.googleplex.com/fuzz_targets/libziparchive_fuzzer/index.html

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
  ZipArchiveHandle handle = nullptr;
  if (OpenArchiveFromMemory(data, size, "fuzz", &handle) == 0) {
    // Iterate through all the entries.
    void* cookie;
    if (StartIteration(handle, &cookie) == 0) {
      ZipEntry ze;
      std::string name;
      int result;
      while ((result = Next(cookie, &ze, &name)) == 0) {
      }
      EndIteration(cookie);
    }
  }
  CloseArchive(handle);
  return 0;
}
