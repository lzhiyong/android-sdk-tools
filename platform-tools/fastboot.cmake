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

add_library(libext4 STATIC
    ${SRC}/extras/ext4_utils/ext4_utils.cpp
    ${SRC}/extras/ext4_utils/wipe.cpp
    ${SRC}/extras/ext4_utils/ext4_sb.cpp
    )
target_include_directories(libext4 PRIVATE
    ${SRC}/core/libsparse/include 
    ${SRC}/core/include 
    ${SRC}/selinux/libselinux/include
    ${SRC}/extras/ext4_utils/include 
    ${SRC}/libbase/include
    )

# Android 17 moved fs_mgr out of platform/system/core into
# platform/system/fs/fs_mgr. Android 16 and earlier keep the old location.
if(EXISTS "${SRC}/fs_mgr/liblp/images.cpp")
    set(FSMGR_ROOT "${SRC}/fs_mgr")
else()
    set(FSMGR_ROOT "${SRC}/core/fs_mgr")
endif()

set(FSMGR_SOURCE_CANDIDATES
    ${FSMGR_ROOT}/liblp/images.cpp
    ${FSMGR_ROOT}/liblp/builder.cpp
    ${FSMGR_ROOT}/liblp/super_layout_builder.cpp
    ${FSMGR_ROOT}/liblp/property_fetcher.cpp
    ${FSMGR_ROOT}/liblp/partition_opener.cpp
    ${FSMGR_ROOT}/liblp/reader.cpp
    ${FSMGR_ROOT}/liblp/utility.cpp
    ${FSMGR_ROOT}/liblp/writer.cpp
)
set(FSMGR_SOURCES)
foreach(source IN LISTS FSMGR_SOURCE_CANDIDATES)
    if(EXISTS "${source}")
        list(APPEND FSMGR_SOURCES "${source}")
    endif()
endforeach()
if(NOT FSMGR_SOURCES)
    message(FATAL_ERROR "No libfsmgr sources found under ${FSMGR_ROOT}/liblp")
endif()
add_library(libfsmgr STATIC ${FSMGR_SOURCES})
target_include_directories(libfsmgr PRIVATE
    ${FSMGR_ROOT}/liblp/include 
    ${SRC}/libbase/include
    ${SRC}/extras/ext4_utils/include 
    ${SRC}/core/libsparse/include
    ${SRC}/boringssl/include
    ${SRC}/core/libcutils/include
    )
target_link_libraries(libfsmgr PUBLIC fmt::fmt)

add_executable(fastboot
    ${SRC}/core/fastboot/bootimg_utils.cpp
    ${SRC}/core/fastboot/fastboot.cpp
    ${SRC}/core/fastboot/fastboot_driver.cpp
    ${SRC}/core/fastboot/fs.cpp
    ${SRC}/core/fastboot/filesystem.cpp
    ${SRC}/core/fastboot/super_flash_helper.cpp
    ${SRC}/core/fastboot/main.cpp
    ${SRC}/core/fastboot/socket.cpp
    ${SRC}/core/fastboot/storage.cpp
    ${SRC}/core/fastboot/task.cpp
    ${SRC}/core/fastboot/tcp.cpp
    ${SRC}/core/fastboot/udp.cpp
    ${SRC}/core/fastboot/usb_linux.cpp
    ${SRC}/core/fastboot/vendor_boot_img_utils.cpp
    ${SRC}/core/fastboot/util.cpp
    )

target_include_directories(fastboot PRIVATE
    ${SRC}/avb
    ${SRC}/libbase/include 
    ${SRC}/soong/cc/libbuildversion/include 
    ${SRC}/core/include 
    ${SRC}/core/adb 
    ${SRC}/core/libsparse/include
    ${FSMGR_ROOT}/liblp/include 
    ${FSMGR_ROOT}/libstorage_literals 
    ${SRC}/libziparchive/include
    ${SRC}/extras/ext4_utils/include 
    ${SRC}/extras/f2fs_utils
    ${SRC}/mkbootimg/include/bootimg
    ${SRC}/core/diagnose_usb/include
    ${SRC}/googletest/googletest/include
    )
target_compile_definitions(fastboot PRIVATE
    -DANDROID_BASE_UNIQUE_FD_DISABLE_IMPLICIT_CONVERSION
    -D_GNU_SOURCE 
    -D_XOPEN_SOURCE=700 
    -DUSE_F2FS
    )
target_link_libraries(fastboot
    libdiagnoseusb
    libsparse
    libziparchive
    libbuildversion
    libcutils
    libfsmgr
    libutils
    libbase
    libext4
    libselinux
    libsepol
    liblog
    crypto
    pcre2-8
    sdk_system_libs
    )