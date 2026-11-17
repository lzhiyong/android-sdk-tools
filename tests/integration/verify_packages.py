#!/usr/bin/env python3
"""Check all four packaged ABI pairs and verify every native tool's ELF machine."""
import argparse
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

ARCHES = {
    "aarch64": ("AArch64", "arm64-v8a"),
    "arm": ("ARM", "armeabi-v7a"),
    "x86_64": ("Advanced Micro Devices X86-64", "x86_64"),
    "i686": ("Intel 80386", "x86"),
}
GROUPS = {
    "platform-tools": ["adb", "fastboot", "sqlite3", "etc1tool", "hprof-conv",
                       "e2fsdroid", "sload_f2fs", "mke2fs", "make_f2fs", "make_f2fs_casefold"],
    "build-tools": ["aapt", "aapt2", "aidl", "dexdump", "split-select", "zipalign"],
    "others": ["veridex"],
}

def check_elf(data, expected, label):
    with tempfile.NamedTemporaryFile() as binary:
        binary.write(data)
        binary.flush()
        result = subprocess.run(["readelf", "-h", binary.name], text=True,
                                capture_output=True, check=True)
    if expected not in result.stdout:
        raise RuntimeError(f"{label}: expected ELF machine {expected}\n{result.stdout}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--directory", type=Path, default=Path("dist"))
    args = parser.parse_args()
    for arch, (machine, abi) in ARCHES.items():
        pt = args.directory / f"platform-tools-{args.version}-{abi}.tar.gz"
        bt = args.directory / f"build-tools-{args.version}-{abi}.zip"
        if not pt.is_file() or not bt.is_file():
            raise RuntimeError(f"Missing archive pair for {arch}: {pt}, {bt}")
        with tarfile.open(pt, "r:gz") as archive:
            for name in GROUPS["platform-tools"]:
                member = archive.extractfile(f"platform-tools/{name}")
                if member is None:
                    raise RuntimeError(f"{pt}: missing platform-tools/{name}")
                check_elf(member.read(), machine, f"{pt}: {name}")
        with zipfile.ZipFile(bt) as archive:
            for group in ("build-tools", "others"):
                for name in GROUPS[group]:
                    path = f"{args.version}/{name}"
                    try:
                        data = archive.read(path)
                    except KeyError as error:
                        raise RuntimeError(f"{bt}: missing {path}") from error
                    check_elf(data, machine, f"{bt}: {name}")
        print(f"PASS: {arch} ({abi}) package contents and ELF architecture")
    print(f"PASS: all 4 ABI package pairs for {args.version}")

if __name__ == "__main__":
    main()
