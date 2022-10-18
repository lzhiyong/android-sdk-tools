/*
 * Copyright (C) 2020 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef ZIPALIGN_H
#define ZIPALIGN_H

namespace android {

/*
 * Generate a new, aligned, zip "output" from an "input" zip.
 * - alignTo: Alignment (in bytes) for uncompressed entries.
 * - force  : Overwrite output if it exists, fail otherwise.
 * - zopfli : Recompress compressed entries with more efficient algorithm.
 *            Copy compressed entries as-is, and unaligned, otherwise.
 * - pageAlignSharedLibs: Align .so files to 4096 and other files to
 *   alignTo, or all files to alignTo if false..
 *
 * Returns 0 on success.
 */
int process(const char* input, const char* output, int alignTo, bool force,
    bool zopfli, bool pageAlignSharedLibs);

/*
 * Verify the alignment of a zip archive.
 * - alignTo: Alignment (in bytes) for uncompressed entries.
 * - pageAlignSharedLibs: Align .so files to 4096 and other files to
 *   alignTo, or all files to alignTo if false..
 *
 * Returns 0 on success.
 */
int verify(const char* fileName, int alignTo, bool verbose,
    bool pageAlignSharedLibs);

} // namespace android

#endif // ZIPALIGN_H
