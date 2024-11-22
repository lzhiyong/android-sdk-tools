#!/usr/bin/env python
#
# Copyright © 2022 Github Lzhiyong
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
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
import zipfile
from pathlib import Path

def format_time(seconds):
    minute, sec = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    
    hour = int(hour)
    minute = int(minute)
    if minute < 1:
        sec = float('%.2f' % sec)
    else:
        sec = int(sec)

    if hour != 0:
        return '{}h{}m{}s'.format(hour, minute, sec)
    elif minute != 0:
        return '{}m{}s'.format(minute, sec)
    else:
        return '{}s'.format(sec)

# package a directory as zip file
def package(srcPathName, destPathName):
    zip = zipfile.ZipFile(destPathName, 'w', zipfile.ZIP_DEFLATED)
    for path, dirs, names in os.walk(srcPathName):
        fpath = path.replace(srcPathName, '')
        for filename in names:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))            
    zip.close()

# build finish
def complete(args):
    # binaries output dir
    binary_dir = Path.cwd() / args.build / 'bin'
    
    # ndk llvm-strip
    strip = Path(args.ndk) / 'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    
    # arch maps
    arch = {
        'arm64-v8a' : 'aarch64', 
        'armeabi-v7a' : 'arm', 
        'x86_64' : 'x86_64', 
        'x86' : 'i686'
    }
    
    # the android tools list
    build_tools = ['aapt', 'aapt2', 'aidl', 'zipalign', 'dexdump', 'split-select']
    
    platform_tools = [
        'adb', 'fastboot', 'sqlite3', 'etc1tool', 'hprof-conv',
        'e2fsdroid', 'sload_f2fs', 'mke2fs', 'make_f2fs', 'make_f2fs_casefold'
    ]
    
    other_tools = ['veridex']
    
    android_tools = {
        binary_dir / 'build-tools' : build_tools,
        binary_dir / 'platform-tools' : platform_tools,
        binary_dir / 'others' : other_tools
    }
    
    # strip debug symbol for android tools
    for (tooldir, tools) in android_tools.items():
        if not tooldir.exists():
            tooldir.mkdir()
        for tool in tools:
            if Path(binary_dir / tool).exists():
                shutil.copy2(binary_dir / tool, tooldir)
                os.remove(binary_dir / tool)
                subprocess.run('{} -g {}'.format(strip, tooldir / tool), shell=True)
    
    # package build tools as a zip file
    package(str(binary_dir), str(binary_dir.parent / 'android-sdk-tools-{}.zip'.format(arch[args.abi])))
    
# start building
def build(args):
    ndk = Path(args.ndk)
    cmake_toolchain_file = ndk / 'build/cmake/android.toolchain.cmake'
    if not cmake_toolchain_file.exists():
        raise ValueError('no such file or directory: {}'.format(cmake_toolchain_file))
        
    command = ['cmake', '-GNinja', 
        '-B {}'.format(args.build),
        '-DANDROID_NDK={}'.format(args.ndk),
        '-DCMAKE_TOOLCHAIN_FILE={}'.format(cmake_toolchain_file),
        '-DANDROID_PLATFORM=android-{}'.format(args.api),
        '-DCMAKE_ANDROID_ARCH_ABI={}'.format(args.abi),
        '-DANDROID_ABI={}'.format(args.abi),
        '-DCMAKE_SYSTEM_NAME=Android',
        '-Dprotobuf_BUILD_TESTS=OFF',
        '-DABSL_PROPAGATE_CXX_STD=ON',
        '-DANDROID_ARM_NEON=ON',
        '-DCMAKE_BUILD_TYPE=Release']
    
    if args.protoc is not None:
        if not Path(args.protoc).exists():
            raise ValueError('no such file or directory: {}'.format(args.protoc))
        command.append('-DPROTOC_PATH={}'.format(args.protoc))
    
    result = subprocess.run(command)
    start_time = time.time()
    if result.returncode == 0:
        if args.target == 'all':
            result = subprocess.run(['ninja', '-C', args.build, '-j {}'.format(args.job)])
        else:
            result = subprocess.run(['ninja', '-C', args.build, args.target, '-j {}'.format(args.job)])

    if result.returncode == 0:
        # build finish
        complete(args)
        end_time = time.time()
        print('\033[1;32mbuild success cost time: {}\033[0m'.format(format_time(end_time - start_time)))
  
def main():
    parser = argparse.ArgumentParser()
    tasks = os.cpu_count()

    parser.add_argument('--ndk', required=True, help='set the ndk toolchain path')

    parser.add_argument('--abi', choices=['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'], 
      required=True, help='build for the specified architecture')
    
    parser.add_argument('--api', default=30, help='set android platform level, min api is 30')

    parser.add_argument('--build', default='build', help='the build directory')

    parser.add_argument('--job', default=tasks, help='run N jobs in parallel, default is {}'.format(tasks))
    
    parser.add_argument('--target', default='all', help='build specified targets such as aapt2 adb fastboot, etc')
    
    parser.add_argument('--protoc', help='set the host protoc path')
    
    args = parser.parse_args()

    build(args)

if __name__ == '__main__':
    main()

