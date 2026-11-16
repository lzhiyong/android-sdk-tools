#!/usr/bin/env python3
"""Package Google's complete Linux SDK archives with this project's binaries."""
import argparse, shutil, subprocess, tarfile, tempfile, zipfile
from pathlib import Path

GROUPS = {
    "platform-tools": ["adb", "e2fsdroid", "etc1tool", "fastboot", "hprof-conv",
                       "make_f2fs", "make_f2fs_casefold", "mke2fs", "sload_f2fs", "sqlite3"],
    "build-tools": ["aapt", "aapt2", "aidl", "dexdump", "split-select", "zipalign"],
    "others": ["veridex"],
}

def download(url, path):
    subprocess.run(["curl", "-fL", "--retry", "3", "--retry-all-errors", "-o", str(path), url], check=True)
    if not zipfile.is_zipfile(path):
        raise RuntimeError("Invalid Google SDK ZIP: " + url)

def extract(path, dest):
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad: raise RuntimeError("Corrupt ZIP member: " + bad)
        z.extractall(dest)

def find_parent(root, filename):
    found = [p.parent for p in root.rglob(filename) if p.is_file()]
    if not found: raise RuntimeError(f"Official archive does not contain {filename}")
    return min(found, key=lambda p: len(p.parts))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--version", required=True)
    p.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    p.add_argument("--output", type=Path, default=Path("dist"))
    a=p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    # Google distributes Linux host tools; use the matching x86_64 build.
    built_zip=next(a.artifacts.rglob("android-sdk-tools-static-x86_64.zip"), None)
    if built_zip is None: raise RuntimeError("x86_64 build artifact is missing")
    with tempfile.TemporaryDirectory(prefix="sdk-package-") as td:
        t=Path(td); built=t/"built"; extract(built_zip,built)
        pt_zip=t/"platform-tools.zip"; bt_zip=t/"build-tools.zip"
        download(f"https://dl.google.com/android/repository/platform-tools_r{a.version}-linux.zip",pt_zip)
        download(f"https://dl.google.com/android/repository/build-tools_r{a.version}_linux.zip",bt_zip)
        pt_ext=t/"pt"; bt_ext=t/"bt"; pt_ext.mkdir(); bt_ext.mkdir()
        extract(pt_zip,pt_ext); extract(bt_zip,bt_ext)
        pt_root=pt_ext/"platform-tools"
        if not pt_root.is_dir(): pt_root=find_parent(pt_ext,"adb")
        bt_root=find_parent(bt_ext,"aapt")
        bt_dest=t/a.version; shutil.copytree(bt_root,bt_dest)
        for group,names in GROUPS.items():
            root=pt_root if group=="platform-tools" else bt_dest
            for name in names:
                src=built/group/name
                if not src.is_file(): raise RuntimeError(f"Built binary missing: {src}")
                dst=root/name; dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,dst); dst.chmod(dst.stat().st_mode|0o111)
                print(f"replaced {group}/{name}")
        pt_out=a.output/f"platform-tools-{a.version}.tar.gz"
        with tarfile.open(pt_out,"w:gz",compresslevel=9) as tf: tf.add(pt_root,arcname="platform-tools")
        bt_out=a.output/f"build-tools-{a.version}.zip"
        with zipfile.ZipFile(bt_out,"w",zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
            for f in sorted(bt_dest.rglob("*")):
                arc=(Path(a.version)/f.relative_to(bt_dest)).as_posix()
                if f.is_dir(): z.writestr(arc+"/",b"")
                else:
                    info=zipfile.ZipInfo.from_file(f,arc)
                    z.writestr(info,f.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
        with tarfile.open(pt_out,"r:gz") as tf:
            members=set(tf.getnames())
            missing={f"platform-tools/{n}" for n in GROUPS["platform-tools"]}-members
            if missing: raise RuntimeError(f"platform-tools package incomplete: {sorted(missing)}")
        with zipfile.ZipFile(bt_out) as z:
            members=set(z.namelist())
            missing={f"{a.version}/{n}" for n in GROUPS["build-tools"]+GROUPS["others"]}-members
            if missing: raise RuntimeError(f"build-tools package incomplete: {sorted(missing)}")
        print(f"created {pt_out}"); print(f"created {bt_out}")

if __name__=="__main__": main()
