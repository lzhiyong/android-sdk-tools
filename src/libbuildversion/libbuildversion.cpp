/*
 * Copyright (C) 2018 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <build/version.h>

#ifdef __ANDROID__
#include <sys/system_properties.h>
#endif

namespace android {
namespace build {

#define PLACEHOLDER "SOONG BUILD NUMBER PLACEHOLDER"

extern "C" {
  char soong_build_number[128] = PLACEHOLDER;
}

#ifdef __ANDROID__

std::string GetBuildNumber() {
  if (strcmp(PLACEHOLDER, soong_build_number) != 0) {
    return soong_build_number;
  }

#ifdef __ANDROID_VENDOR__
  const prop_info* pi = __system_property_find("ro.vendor.build.version.incremental");
#else
  const prop_info* pi = __system_property_find("ro.build.version.incremental");
#endif
  if (pi == nullptr) return "";

  std::string property_value;
  __system_property_read_callback(pi,
                                  [](void* cookie, const char*, const char* value, unsigned) {
                                    auto property_value = reinterpret_cast<std::string*>(cookie);
                                    *property_value = value;
                                  },
                                  &property_value);

  return property_value;
}

#else

std::string GetBuildNumber() {
  return soong_build_number;
}

#endif
}  // namespace build
}  // namespace android
