zipalign -- zip archive alignment tool

usage: zipalign [-f] [-v] <align> infile.zip outfile.zip
       zipalign -c [-v] <align> infile.zip

  -c : check alignment only (does not modify file)
  -f : overwrite existing outfile.zip
  -p : page align stored shared object files
  -v : verbose output
  <align> is in bytes, e.g. "4" provides 32-bit alignment
  infile.zip is an existing Zip archive
  outfile.zip will be created


The purpose of zipalign is to ensure that all uncompressed data starts
with a particular alignment relative to the start of the file.  This
allows those portions to be accessed directly with mmap() even if they
contain binary data with alignment restrictions.

Some data needs to be word-aligned for easy access, others might benefit
from being page-aligned.  The adjustment is made by altering the size of
the "extra" field in the zip Local File Header sections.  Existing data
in the "extra" fields may be altered by this process.

Compressed data isn't very useful until it's uncompressed, so there's no
need to adjust its alignment.

Alterations to the archive, such as renaming or deleting entries, will
potentially disrupt the alignment of the modified entry and all later
entries.  Files added to an "aligned" archive will not be aligned.

By default, zipalign will not overwrite an existing output file.  With the
"-f" flag, an existing file will be overwritten.

You can use the "-c" flag to test whether a zip archive is properly aligned.

The "-p" flag aligns any file with a ".so" extension, and which is stored
uncompressed in the zip archive, to a 4096-byte page boundary.  This
facilitates directly loading shared libraries from inside a zip archive.

