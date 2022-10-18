/*
 * Copyright (C) 2008 The Android Open Source Project
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

#include "ZipFile.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

namespace android {

static int getAlignment(bool pageAlignSharedLibs, int defaultAlignment,
    ZipEntry* pEntry) {

    static const int kPageAlignment = 4096;

    if (!pageAlignSharedLibs) {
        return defaultAlignment;
    }

    const char* ext = strrchr(pEntry->getFileName(), '.');
    if (ext && strcmp(ext, ".so") == 0) {
        return kPageAlignment;
    }

    return defaultAlignment;
}

/*
 * Copy all entries from "pZin" to "pZout", aligning as needed.
 */
static int copyAndAlign(ZipFile* pZin, ZipFile* pZout, int alignment, bool zopfli,
    bool pageAlignSharedLibs)
{
    int numEntries = pZin->getNumEntries();
    ZipEntry* pEntry;
    status_t status;

    for (int i = 0; i < numEntries; i++) {
        ZipEntry* pNewEntry;
        int padding = 0;

        pEntry = pZin->getEntryByIndex(i);
        if (pEntry == NULL) {
            fprintf(stderr, "ERROR: unable to retrieve entry %d\n", i);
            return 1;
        }

        if (pEntry->isCompressed()) {
            /* copy the entry without padding */
            //printf("--- %s: orig at %ld len=%ld (compressed)\n",
            //    pEntry->getFileName(), (long) pEntry->getFileOffset(),
            //    (long) pEntry->getUncompressedLen());

            if (zopfli) {
                status = pZout->addRecompress(pZin, pEntry, &pNewEntry);
            } else {
                status = pZout->add(pZin, pEntry, padding, &pNewEntry);
            }
        } else {
            const int alignTo = getAlignment(pageAlignSharedLibs, alignment, pEntry);

            //printf("--- %s: orig at %ld(+%d) len=%ld, adding pad=%d\n",
            //    pEntry->getFileName(), (long) pEntry->getFileOffset(),
            //    bias, (long) pEntry->getUncompressedLen(), padding);
            status = pZout->add(pZin, pEntry, alignTo, &pNewEntry);
        }

        if (status != OK)
            return 1;
        //printf(" added '%s' at %ld (pad=%d)\n",
        //    pNewEntry->getFileName(), (long) pNewEntry->getFileOffset(),
        //    padding);
    }

    return 0;
}

/*
 * Process a file.  We open the input and output files, failing if the
 * output file exists and "force" wasn't specified.
 */
int process(const char* inFileName, const char* outFileName,
    int alignment, bool force, bool zopfli, bool pageAlignSharedLibs)
{
    ZipFile zin, zout;

    //printf("PROCESS: align=%d in='%s' out='%s' force=%d\n",
    //    alignment, inFileName, outFileName, force);

    /* this mode isn't supported -- do a trivial check */
    if (strcmp(inFileName, outFileName) == 0) {
        fprintf(stderr, "Input and output can't be same file\n");
        return 1;
    }

    /* don't overwrite existing unless given permission */
    if (!force && access(outFileName, F_OK) == 0) {
        fprintf(stderr, "Output file '%s' exists\n", outFileName);
        return 1;
    }

    if (zin.open(inFileName, ZipFile::kOpenReadOnly) != OK) {
        fprintf(stderr, "Unable to open '%s' as zip archive\n", inFileName);
        return 1;
    }
    if (zout.open(outFileName,
            ZipFile::kOpenReadWrite|ZipFile::kOpenCreate|ZipFile::kOpenTruncate)
        != OK)
    {
        fprintf(stderr, "Unable to open '%s' as zip archive\n", outFileName);
        return 1;
    }

    int result = copyAndAlign(&zin, &zout, alignment, zopfli, pageAlignSharedLibs);
    if (result != 0) {
        printf("zipalign: failed rewriting '%s' to '%s'\n",
            inFileName, outFileName);
    }
    return result;
}

/*
 * Verify the alignment of a zip archive.
 */
int verify(const char* fileName, int alignment, bool verbose,
    bool pageAlignSharedLibs)
{
    ZipFile zipFile;
    bool foundBad = false;

    if (verbose)
        printf("Verifying alignment of %s (%d)...\n", fileName, alignment);

    if (zipFile.open(fileName, ZipFile::kOpenReadOnly) != OK) {
        fprintf(stderr, "Unable to open '%s' for verification\n", fileName);
        return 1;
    }

    int numEntries = zipFile.getNumEntries();
    ZipEntry* pEntry;

    for (int i = 0; i < numEntries; i++) {
        pEntry = zipFile.getEntryByIndex(i);
        if (pEntry->isCompressed()) {
            if (verbose) {
                printf("%8jd %s (OK - compressed)\n",
                    (intmax_t) pEntry->getFileOffset(), pEntry->getFileName());
            }
        } else {
            off_t offset = pEntry->getFileOffset();
            const int alignTo = getAlignment(pageAlignSharedLibs, alignment, pEntry);
            if ((offset % alignTo) != 0) {
                if (verbose) {
                    printf("%8jd %s (BAD - %jd)\n",
                        (intmax_t) offset, pEntry->getFileName(),
                        (intmax_t) (offset % alignTo));
                }
                foundBad = true;
            } else {
                if (verbose) {
                    printf("%8jd %s (OK)\n",
                        (intmax_t) offset, pEntry->getFileName());
                }
            }
        }
    }

    if (verbose)
        printf("Verification %s\n", foundBad ? "FAILED" : "succesful");

    return foundBad ? 1 : 0;
}

} // namespace android
