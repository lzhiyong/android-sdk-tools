#!/bin/bash

# Copy the tests across.
test_dir=/data/local/tests/unrestricted/ziptool-tests

# TODO(b/169618311): remove this "adb push" command.
adb push cli-tests/ "$test_dir"

if tty -s; then
  dash_t="-t"
else
  dash_t=""
fi

exec adb shell "$dash_t" "${test_dir}"/cli-test "${test_dir}"/cli-tests/*.test
