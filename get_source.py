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
import requests
import tarfile
import shutil
import argparse
import subprocess
from pathlib import Path


def untar(source, target):
    tar = tarfile.open(source)
    names = tar.getnames()
    if os.path.isdir(target):
        pass
    else:
        os.mkdir(target)

    for name in names:
        tar.extract(name, target)
    tar.close()

def download(url, filename, target):
    print("downloading {}".format(filename))
    content = requests.get(url).content
    with open(filename, 'wb') as file:
        file.write(content)
    # extract tar file
    print("extracting {} to {}".format(filename, target))
    untar(filename, target)
    # delete file
    if os.path.exists(filename):
        os.remove(filename)

def patches():
    inc = Path(os.getcwd() + "/src/incremental_delivery/sysprop/include")
    if not inc.exists():
        inc.mkdir()
    shutil.copy2(Path("patches/misc/IncrementalProperties.sysprop.h"), inc)
    shutil.copy2(Path("patches/misc/IncrementalProperties.sysprop.cpp"), inc.parent)

    shutil.copy2(Path("patches/misc/deployagent.inc"), Path("src/adb/fastdeploy/deployagent"))
    shutil.copy2(Path("patches/misc/deployagentscript.inc"), Path("src/adb/fastdeploy/deployagent"))

    shutil.copy2(Path("patches/misc/platform_tools_version.h"), Path("src/libbuildversion/include"))
    
    pattern = "\'s/frameworks\/base\/tools\/aapt2\/Configuration\.proto/Configuration\.proto/g\'"
    pattern2 = "\'s/frameworks\/base\/tools\/aapt2\/Resources\.proto/Resources\.proto/g\'"
    subprocess.run("sed -i {} {}".format(pattern, os.getcwd() + "/src/base/tools/aapt2/Resources.proto"), shell=True)
    subprocess.run("sed -i {} {}".format(pattern, os.getcwd() + "/src/base/tools/aapt2/ResourcesInternal.proto"), shell=True)
    subprocess.run("sed -i {} {}".format(pattern2, os.getcwd() + "/src/base/tools/aapt2/ResourcesInternal.proto"), shell=True)
    
    pattern3 = "\'s/\/usr\/src\/googletest/\$\{CMAKE_SOURCE_DIR\}\/src\/googletest/g\'"
    subprocess.run("sed -i {} {}".format(pattern3, os.getcwd() + "/src/abseil-cpp/CMakeLists.txt"), shell=True)

def check(command):
    try:
        output = subprocess.check_output("command -v {}".format(command), shell=True)
        print(output.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print("please install the {} package".format(command))
        exit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tags", help="Specify Git cloning tags or branch")
    args = parser.parse_args()
    
    # check git
    check("git")
    # check golang
    check("go")
    
    # tags platform-tools-33.0.3
    # libziparchive
    url = "https://android.googlesource.com/platform/system/libziparchive/+archive/9b2d511d0f3d656f879d18bdc542f7860f53aab6.tar.gz"
    download(url, os.path.basename(url), "src/libziparchive")

    # zipalign
    url = "https://android.googlesource.com/platform/build.git/+archive/refs/tags/platform-tools-33.0.3/tools/zipalign.tar.gz"
    download(url, os.path.basename(url), "src/zipalign")

    # etc1tool
    url = "https://android.googlesource.com/platform/development/+archive/refs/tags/platform-tools-33.0.3/tools/etc1tool.tar.gz"
    download(url, os.path.basename(url), "src/etc1tool")

    # libbuildversion
    url = "https://android.googlesource.com/platform/build/soong/+archive/refs/tags/platform-tools-33.0.3/cc/libbuildversion.tar.gz"
    download(url, os.path.basename(url), "src/libbuildversion")
    
    # git clone submodules
    subprocess.run("git submodule update --depth=1 --init --recursive --remote", shell=True)
    
    if args.tags is not None:
        subprocess.run("git submodule foreach git fetch origin refs/tags/{}".format(args.tags), shell=True)
        subprocess.run("git submodule foreach git checkout tags/{}".format(args.tags), shell=True)
    else:
        subprocess.run("git submodule foreach git checkout -b master", shell=True)
    
    # patch files
    patches()
    
    print("download success!!")

if __name__ == "__main__":
    main()
 
