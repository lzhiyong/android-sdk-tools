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

set(LIBBASE_SOURCE_CANDIDATES
    ${CMAKE_CURRENT_LIST_DIR}/libbase_result_compat.cpp
    ${SRC}/libbase/abi_compatibility.cpp
    ${SRC}/libbase/chrono_utils.cpp
    ${SRC}/libbase/cmsg.cpp
    ${SRC}/libbase/file.cpp
    ${SRC}/libbase/hex.cpp
    ${SRC}/libbase/logging.cpp
    ${SRC}/libbase/mapped_file.cpp
    ${SRC}/libbase/parsebool.cpp
    ${SRC}/libbase/parsenetaddress.cpp
    ${SRC}/libbase/posix_strerror_r.cpp
    ${SRC}/libbase/process.cpp
    ${SRC}/libbase/properties.cpp
    ${SRC}/libbase/stringprintf.cpp
    ${SRC}/libbase/strings.cpp
    ${SRC}/libbase/threads.cpp
    ${SRC}/libbase/test_utils.cpp
    ${SRC}/libbase/errors_unix.cpp
)

set(LIBBASE_SOURCES)
foreach(source IN LISTS LIBBASE_SOURCE_CANDIDATES)
    if(EXISTS "${source}")
        list(APPEND LIBBASE_SOURCES "${source}")
    endif()
endforeach()

if(NOT LIBBASE_SOURCES)
    message(FATAL_ERROR "No libbase sources found under ${SRC}/libbase")
endif()

add_library(libbase STATIC ${LIBBASE_SOURCES})

target_include_directories(libbase PRIVATE
    ${SRC}/libbase/include
    ${SRC}/core/include
    ${SRC}/fmtlib/include
    ${SRC}/logging/liblog/include
)
