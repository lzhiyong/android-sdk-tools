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

/*
 * Zip alignment tool
 */

#include "ZipAlign.h"

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>

using namespace android;

/*
 * Show program usage.
 */
void usage(void)
{
    fprintf(stderr, "Zip alignment utility\n");
    fprintf(stderr, "Copyright (C) 2009 The Android Open Source Project\n\n");
    fprintf(stderr,
        "Usage: zipalign [-f] [-p] [-v] [-z] <align> infile.zip outfile.zip\n"
        "       zipalign -c [-p] [-v] <align> infile.zip\n\n" );
    fprintf(stderr,
        "  <align>: alignment in bytes, e.g. '4' provides 32-bit alignment\n");
    fprintf(stderr, "  -c: check alignment only (does not modify file)\n");
    fprintf(stderr, "  -f: overwrite existing outfile.zip\n");
    fprintf(stderr, "  -p: page-align uncompressed .so files\n");
    fprintf(stderr, "  -v: verbose output\n");
    fprintf(stderr, "  -z: recompress using Zopfli\n");
}


/*
 * Parse args.
 */
int main(int argc, char* const argv[])
{
    bool wantUsage = false;
    bool check = false;
    bool force = false;
    bool verbose = false;
    bool zopfli = false;
    bool pageAlignSharedLibs = false;
    int result = 1;
    int alignment;
    char* endp;

    int opt;
    while ((opt = getopt(argc, argv, "fcpvz")) != -1) {
        switch (opt) {
        case 'c':
            check = true;
            break;
        case 'f':
            force = true;
            break;
        case 'v':
            verbose = true;
            break;
        case 'z':
            zopfli = true;
            break;
        case 'p':
            pageAlignSharedLibs = true;
            break;
        default:
            fprintf(stderr, "ERROR: unknown flag -%c\n", opt);
            wantUsage = true;
            goto bail;
        }
    }

    if (!((check && (argc - optind) == 2) || (!check && (argc - optind) == 3))) {
        wantUsage = true;
        goto bail;
    }

    alignment = strtol(argv[optind], &endp, 10);
    if (*endp != '\0' || alignment <= 0) {
        fprintf(stderr, "Invalid value for alignment: %s\n", argv[optind]);
        wantUsage = true;
        goto bail;
    }

    if (check) {
        /* check existing archive for correct alignment */
        result = verify(argv[optind + 1], alignment, verbose, pageAlignSharedLibs);
    } else {
        /* create the new archive */
        result = process(argv[optind + 1], argv[optind + 2], alignment, force, zopfli, pageAlignSharedLibs);

        /* trust, but verify */
        if (result == 0) {
            result = verify(argv[optind + 2], alignment, verbose, pageAlignSharedLibs);
        }
    }

bail:
    if (wantUsage) {
        usage();
        result = 2;
    }

    return result;
}
