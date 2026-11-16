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

# Android 15 and earlier used the cgrouprc_format/cgrouprc source layout.
# Android 16+ consolidated the implementation under cgrouprc/ and util/.
# Keep both layouts supported and only pass files present in the selected tag.
set(LIBPROCESSGROUP_SOURCE_CANDIDATES
    ${SRC}/core/libprocessgroup/cgroup_map.cpp
    ${SRC}/core/libprocessgroup/processgroup.cpp
    ${SRC}/core/libprocessgroup/sched_policy.cpp
    ${SRC}/core/libprocessgroup/task_profiles.cpp
    ${SRC}/core/libprocessgroup/cgrouprc_format/cgroup_controller.cpp
    ${SRC}/core/libprocessgroup/cgrouprc/cgroup_controller.cpp
    ${SRC}/core/libprocessgroup/cgrouprc/cgroup_file.cpp
    ${SRC}/core/libprocessgroup/cgrouprc/a_cgroup_controller.cpp
    ${SRC}/core/libprocessgroup/cgrouprc/a_cgroup_file.cpp
    ${SRC}/core/libprocessgroup/util/cgroup_controller.cpp
    ${SRC}/core/libprocessgroup/util/cgroup_descriptor.cpp
    ${SRC}/core/libprocessgroup/util/util.cpp
)

set(LIBPROCESSGROUP_SOURCES)
foreach(source IN LISTS LIBPROCESSGROUP_SOURCE_CANDIDATES)
    if(EXISTS "${source}")
        list(APPEND LIBPROCESSGROUP_SOURCES "${source}")
    endif()
endforeach()

if(NOT LIBPROCESSGROUP_SOURCES)
    message(FATAL_ERROR "No libprocessgroup sources found under ${SRC}/core/libprocessgroup")
endif()

add_library(libprocessgroup STATIC ${LIBPROCESSGROUP_SOURCES})

target_include_directories(libprocessgroup PRIVATE
    ${SRC}/core/libprocessgroup/include
    ${SRC}/core/libprocessgroup/cgrouprc/include
    ${SRC}/core/libprocessgroup/cgrouprc_format/include
    ${SRC}/core/libprocessgroup/util/include
    ${SRC}/libbase/include
    ${SRC}/core/libcutils/include
    ${SRC}/jsoncpp/include
)
target_include_directories(libprocessgroup PRIVATE
    ${SRC}/core/libprocessgroup
)
