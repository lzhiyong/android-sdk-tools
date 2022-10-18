#!/usr/bin/env python
#
# Copyright © 2022 Github Lzhiyong
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
# pylint: disable=not-callable, line-too-long, no-else-return

import os
import time
import shutil
import argparse
import subprocess
from pathlib import Path

def format_time(seconds):
    minute, sec = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    
    hour = int(hour)
    minute = int(minute)
    sec = float('%.2f' % sec)
    if hour != 0:
        return "{}h{}m{}s".format(hour, minute, sec)
    elif minute != 0:
        return "{}m{}s".format(minute, sec)
    else:
        return "{}s".format(sec)

def finish(args):
    cwd = Path(os.getcwd())
    strip = args.ndk + "/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip"

    build_tools_dir = cwd / "{}/bin/build-tools".format(args.build)
    if not build_tools_dir.exists():
        build_tools_dir.mkdir()

    platform_tools_dir = cwd / "{}/bin/platform-tools".format(args.build)
    if not platform_tools_dir.exists():
        platform_tools_dir.mkdir()

    build_tools = ['aapt', 'aapt2', 'aidl', 'zipalign', 'dexdump', 'split-select']
    for tool in build_tools:
        if Path(build_tools_dir.parent / tool).exists():
            shutil.copy2(build_tools_dir.parent / tool, build_tools_dir)
            os.remove(build_tools_dir.parent / tool)
            subprocess.run("{} -g {}".format(strip, build_tools_dir / tool), shell=True)

    platform_tools = [
        'adb', 'fastboot', 'sqlite3', 'dmtracedump', 'etc1tool', 'hprof-conv',
        'e2fsdroid', 'sload_f2fs', 'mke2fs', 'make_f2fs', 'make_f2fs_casefold'
    ]
    for tool in platform_tools:
        if Path(platform_tools_dir.parent / tool).exists():
            shutil.copy2(platform_tools_dir.parent / tool, platform_tools_dir)
            os.remove(build_tools_dir.parent / tool)
            subprocess.run("{} -g {}".format(strip, platform_tools_dir / tool), shell=True)


def build(args):
    ndk = Path(args.ndk)
    cmake_toolchain_file = ndk / "build/cmake/android.toolchain.cmake"
    if not cmake_toolchain_file.exists():
        raise ValueError("no such file or directory: {}".format(cmake_toolchain_file))
        
    command = ["cmake", "-GNinja", 
        "-B {}".format(args.build),
        "-DANDROID_NDK={}".format(args.ndk),
        "-DCMAKE_TOOLCHAIN_FILE={}".format(cmake_toolchain_file),
        "-DANDROID_PLATFORM=android-{}".format(args.api),
        "-DCMAKE_ANDROID_ARCH_ABI={}".format(args.abi),
        "-DANDROID_ABI={}".format(args.abi),
        "-DCMAKE_SYSTEM_NAME=Android",
        "-Dprotobuf_BUILD_TESTS=OFF",
        "-DABSL_PROPAGATE_CXX_STD=ON",
        "-DANDROID_ARM_NEON=ON",
        "-DCMAKE_BUILD_TYPE=Release"]
    
    if args.protoc is not None:
        if not Path(args.protoc).exists():
            raise ValueError("no such file or directory: {}".format(args.protoc))
        command.append("-DPROTOC_PATH={}".format(args.protoc))
    
    result = subprocess.run(command)
    start = time.time()
    if result.returncode == 0:
        if args.target == "all":
            result = subprocess.run(["ninja", "-C", args.build, "-j {}".format(args.job)])
        else:
            result = subprocess.run(["ninja", "-C", args.build, args.target, "-j {}".format(args.job)])

    if result.returncode == 0:
        # build finish
        finish(args)
        end = time.time()
        print("\033[1;32mbuild success cost time: {}\033[0m".format(format_time(end - start)))

    
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--ndk", required=True, help="set the ndk toolchain path")

    parser.add_argument("--abi", choices=["armeabi-v7a", "arm64-v8a", "x86", "x86_64"], 
      required=True, help="build for the specified architecture")
    
    parser.add_argument("--api", default=30, help="set android platform level, min api is 30")

    parser.add_argument("--build", default="build", help="the build directory")

    parser.add_argument("--job", default=16, help="run N jobs in parallel, default is 16")
    
    parser.add_argument("--target", default="all", help="build specified targets such as aapt2 adb fastboot, etc")
    
    parser.add_argument("--protoc", help="set the host protoc path")
    
    args = parser.parse_args()

    build(args)

if __name__ == "__main__":
    main()
