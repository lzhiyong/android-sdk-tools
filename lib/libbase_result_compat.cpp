/*
 * Copyright (C) 2026 ZeroStudio
 * Licensed under the Apache License, Version 2.0.
 */
#include <android-base/result.h>

#include <utility>

namespace android {
namespace base {

// platform-tools-35.0.1 declares this helper in result.h but does not ship
// result.cpp in the pinned libbase source snapshot. Keep the out-of-line
// implementation here so callers from fastboot and libbase resolve it.
ResultError<Errno> MakeResultErrorWithCode(std::string&& message, Errno code) {
    return ResultError(std::move(message) + ": " + code.print(), code);
}

}  // namespace base
}  // namespace android
