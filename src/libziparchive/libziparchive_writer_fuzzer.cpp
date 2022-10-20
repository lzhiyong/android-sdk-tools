// SPDX-License-Identifier: Apache-2.0

#include <stddef.h>
#include <stdint.h>

#include "fuzzer/FuzzedDataProvider.h"
#include <android-base/file.h>
#include <ziparchive/zip_writer.h>

// See current fuzz coverage here:
// https://android-coverage.googleplex.com/fuzz_targets/libziparchive_writer_fuzzer/index.html

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
  FuzzedDataProvider provider(data, size);
  std::unique_ptr<std::FILE, decltype(&fclose)> fp(tmpfile(), &fclose);
  if (!fp) {
    return 0;
  }
  ZipWriter writer(fp.get());
  for (int i = 0; i < 2; i++) {
    if (provider.remaining_bytes() == 0) {
      break;
    }
    auto path = provider.ConsumeRandomLengthString();
    if (writer.StartEntry(path, path.size()) == 0) {
      for (int j = 0; j < 2; j++) {
        if (provider.remaining_bytes() == 0) {
          break;
        }
        const size_t next_size = provider.ConsumeIntegralInRange<size_t>(
            0, provider.remaining_bytes());
        auto next_buf = provider.ConsumeBytes<uint8_t>(next_size);
        writer.WriteBytes(next_buf.data(), next_buf.size());
      }
      writer.FinishEntry();
    }
  }
  writer.Finish();
  return 0;
}
