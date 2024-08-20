Building platform-tools and build-tools for Android, such as `aapt aapt2 aidl zipalign adb fastboot` ... etc.

If you need other tools, please refer to existing tools to add CMake file.

Currently, only aarch64 has been tested, and it is not guaranteed to work for other architectures.

In order to save storage and bandwidth, I have removed all submodules and no longer provide source code compressed packages.

I believe that as long as you have the C/C++ and CMake foundation, it can be easily solved by referring to the patch files.

 **** 
 
### How to build
First, we need to use `get_source.py` to clone the source code of all repositories.

Please note that patch files only apply to specific branches or tags, so we may need to patch manually.

```bash
# default is master branch
python get_source.py

# specific branches or tags
python get_source.py --tags platform-tools-35.0.2

# or tags xxx
# see available tags https://android.googlesource.com/platform/frameworks/base/+refs
python get_source.py --tags xxx

```

 **** 

Second, we need to build `protobuf` for the host OS which will be used to generate the required sources.

```bash
# protobuf source directory
cd src/protobuf && mkdir build && cd build

# skip the googletest
cmake -GNinja -Dprotobuf_BUILD_TESTS=OFF ..

# building the protoc-xxx executable file
ninja -j$(nproc --all)

```

 **** 
 
Finally, we can use the `NDK` to start building the Android SDK Tools.

Please note that it is only applicable to Android ndk for compilation, not applicable to other Linux distributions.

```bash
# abi [arm64-v8a, armeabi-v7a, x86, x86_64]
# use the protoc-xxx we compiled before
# note the protoc requires absolute path
python build.py \
    --ndk=/path/to/android-ndk-xxx \
    --abi=arm64-v8a \
    --build=build/aarch64 \
    --protoc=/path/to/protoc-xxx
    
# I think you should build each target separately for better error resolution
# like appt2 adb fastboot...etc
python build.py \
    --ndk=/path/to/android-ndk-xxx \
    --abi=arm64-v8a \
    --build=build/aarch64 \
    --protoc=/path/to/protoc-xxx \
    --target=aapt2

# for other options, please execute
python build.py --help

```

 **** 
 
