#!/usr/bin/env python3
"""Package complete Google Linux SDK archives with one ABI's native tools."""
import argparse
import re
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

ARCHES = {
    "aarch64": "arm64-v8a",
    "arm": "armeabi-v7a",
    "x86_64": "x86_64",
    "i686": "x86",
}
GROUPS = {
    "platform-tools": ["adb", "e2fsdroid", "etc1tool", "fastboot", "hprof-conv",
                       "make_f2fs", "make_f2fs_casefold", "mke2fs", "sload_f2fs", "sqlite3"],
    "build-tools": ["aapt", "aapt2", "aidl", "dexdump", "split-select", "zipalign"],
    "others": ["veridex"],
}


def download(url, path):
    subprocess.run(
        ["curl", "-fL", "--retry", "3", "--retry-all-errors", "-o", str(path), url],
        check=True,
    )
    if not zipfile.is_zipfile(path):
        raise RuntimeError("Invalid Google SDK ZIP: " + url)


def download_first_available(urls, path):
    """Download the first published official archive from an ordered URL list."""
    for url in urls:
        result = subprocess.run(
            ["curl", "-fLsS", "--retry", "0", "-o", str(path), url],
            check=False,
        )
        if result.returncode == 0 and zipfile.is_zipfile(path):
            print("Using official SDK archive:", url)
            return
        path.unlink(missing_ok=True)
    raise RuntimeError("No published official Build Tools archive found: " + ", ".join(urls))


def extract(path, dest):
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError("Corrupt ZIP member: " + bad)
        archive.extractall(dest)


def find_parent(root, filename):
    found = [p.parent for p in root.rglob(filename) if p.is_file()]
    if not found:
        raise RuntimeError(f"Official archive does not contain {filename}")
    return min(found, key=lambda p: len(p.parts))



def update_pkg_revision(sdk_root, version):
    """Set the SDK package metadata revision to the version being packaged."""
    properties = sdk_root / "source.properties"
    if not properties.is_file():
        raise RuntimeError(f"SDK source.properties missing: {properties}")
    content = properties.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"(?m)^Pkg\.Revision\s*=.*$",
        f"Pkg.Revision={version}",
        content,
    )
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one Pkg.Revision in {properties}, found {count}"
        )
    properties.write_text(updated, encoding="utf-8")
    if f"Pkg.Revision={version}" not in properties.read_text(encoding="utf-8"):
        raise RuntimeError(f"Failed to update package revision in {properties}")
    print(f"updated {properties}: Pkg.Revision={version}")

def create_build_tools_zip(source, output, version):
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9, allowZip64=True) as archive:
        for path in sorted(source.rglob("*")):
            name = (Path(version) / path.relative_to(source)).as_posix()
            if path.is_dir():
                archive.writestr(name + "/", b"")
            else:
                info = zipfile.ZipInfo.from_file(path, name)
                archive.writestr(info, path.read_bytes(),
                                 compress_type=zipfile.ZIP_DEFLATED,
                                 compresslevel=9)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="sdk-package-") as temp:
        root = Path(temp)
        pt_zip = root / "platform-tools.zip"
        bt_zip = root / "build-tools.zip"
        # Platform Tools 37.0.2 never graduated beyond Canary; Google only
        # publishes the 37.0.1 stable archive. Use it as the untouched base and
        # replace the native executables with the branch's 37.0.2 builds below.
        platform_tools_versions = [args.version]
        if args.version == "37.0.2":
            platform_tools_versions.append("37.0.1")
        platform_tools_urls = [
            f"https://dl.google.com/android/repository/platform-tools_r{version}-linux.zip"
            for version in platform_tools_versions
        ]
        download_first_available(platform_tools_urls, pt_zip)
        # Platform Tools and Build Tools have independent release trains.
        # Prefer an exact matching Build Tools archive, then the official major
        # release archive, followed by published preview archives for that major.
        major = args.version.split(".", 1)[0]
        build_tools_versions = []
        exact = args.version
        if exact.endswith(".0.0"):
            exact = exact.rsplit(".", 2)[0]
        build_tools_versions.append(exact)
        build_tools_versions.append(major)
        build_tools_versions.extend([f"{major}-rc2", f"{major}-rc1"])
        # Android Gradle Plugin 9.x still specifies Build Tools 36.0.0 as its
        # default for API 37; no official Build Tools 37.x archive is published.
        if int(major) >= 36:
            build_tools_versions.append("36.0.0")
        # Keep order while removing duplicate candidates.
        build_tools_versions = list(dict.fromkeys(build_tools_versions))
        build_tools_urls = [
            f"https://dl.google.com/android/repository/build-tools_r{version}-linux.zip"
            for version in build_tools_versions
        ]
        download_first_available(build_tools_urls, bt_zip)

        pt_extract = root / "platform-tools-extracted"
        bt_extract = root / "build-tools-extracted"
        pt_extract.mkdir()
        bt_extract.mkdir()
        extract(pt_zip, pt_extract)
        extract(bt_zip, bt_extract)

        official_pt = pt_extract / "platform-tools"
        if not official_pt.is_dir():
            official_pt = find_parent(pt_extract, "adb")
        official_bt = find_parent(bt_extract, "aapt")

        for build_arch, abi in ARCHES.items():
            artifact = next(
                args.artifacts.rglob(f"android-sdk-tools-static-{build_arch}.zip"),
                None,
            )
            if artifact is None:
                raise RuntimeError(f"Build artifact missing for {build_arch}: {abi}")

            built_root = root / f"built-{build_arch}"
            extract(artifact, built_root)

            pt_root = root / f"pt-{abi}"
            bt_root = root / f"bt-{abi}"
            shutil.copytree(official_pt, pt_root)
            shutil.copytree(official_bt, bt_root)

            # Keep the official Java tools/resources intact; adapt only launcher shebangs
            # for Android's shell environment.
            for launcher in ("d8", "apksigner"):
                launcher_path = bt_root / launcher
                if launcher_path.is_file():
                    data = launcher_path.read_bytes()
                    if data.startswith(b"#!"):
                        _, separator, remainder = data.partition(b"\\n")
                        if separator:
                            launcher_path.write_bytes(b"#!/system/bin/env sh\n" + remainder)

            for group, names in GROUPS.items():
                destination_root = pt_root if group == "platform-tools" else bt_root
                for name in names:
                    source = built_root / group / name
                    if not source.is_file():
                        raise RuntimeError(f"{abi}: built binary missing: {source}")
                    destination = destination_root / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
                    destination.chmod(0o755)
                    print(f"[{abi}] replaced {group}/{name} mode=755")

            # Rewrite metadata only after all custom native binaries are installed.
            update_pkg_revision(pt_root, args.version)
            update_pkg_revision(bt_root, args.version)

            pt_output = args.output / f"platform-tools-{args.version}-{abi}.tar.gz"
            with tarfile.open(pt_output, "w:gz", compresslevel=9) as archive:
                archive.add(pt_root, arcname="platform-tools")

            bt_output = args.output / f"build-tools-{args.version}-{abi}.zip"
            create_build_tools_zip(bt_root, bt_output, args.version)

            with tarfile.open(pt_output, "r:gz") as archive:
                pt_metadata = archive.extractfile("platform-tools/source.properties")
                if pt_metadata is None or f"Pkg.Revision={args.version}".encode() not in pt_metadata.read():
                    raise RuntimeError(f"{abi}: platform-tools source.properties has the wrong Pkg.Revision")
                members = set(archive.getnames())
                missing = {
                    f"platform-tools/{name}" for name in GROUPS["platform-tools"]
                } - members
                if missing:
                    raise RuntimeError(f"{abi}: platform-tools archive missing {sorted(missing)}")

            with zipfile.ZipFile(bt_output) as archive:
                bt_metadata = archive.read(f"{args.version}/source.properties")
                if f"Pkg.Revision={args.version}".encode() not in bt_metadata:
                    raise RuntimeError(f"{abi}: build-tools source.properties has the wrong Pkg.Revision")
                members = set(archive.namelist())
                missing = {
                    f"{args.version}/{name}"
                    for name in GROUPS["build-tools"] + GROUPS["others"]
                } - members
                if missing:
                    raise RuntimeError(f"{abi}: build-tools archive missing {sorted(missing)}")

            print(f"created {pt_output}")
            print(f"created {bt_output}")


if __name__ == "__main__":
    main()
