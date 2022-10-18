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

#include <stdio.h>

#include <gtest/gtest.h>

#include <build/version.h>

#include "build_version_test_lib.h"

TEST(BuildNumber, binary) {
  printf("binary version: %s\n", android::build::GetBuildNumber().c_str());
  EXPECT_NE(android::build::GetBuildNumber(), "SOONG BUILD NUMBER PLACEHOLDER");
}

  // symbol_inject doesn't support dlls
#ifndef __WIN32__
TEST(BuildNumber, library) {
  printf("shared library version: %s\n", LibGetBuildNumber().c_str());
  EXPECT_NE(LibGetBuildNumber(), "SOONG BUILD NUMBER PLACEHOLDER");
}
#endif
