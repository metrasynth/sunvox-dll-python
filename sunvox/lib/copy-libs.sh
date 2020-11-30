#!/usr/bin/env bash
#
# Copies libs from the SunVox library distribution.

set -euxo pipefail

usage() {
    echo "Usage: $0 <sunvox-library-dir>"
    exit 1
}

[[ "$*" != "" ]] || usage

SUNVOX_LIB_DIR="$1"

[[ -d "${SUNVOX_LIB_DIR}" ]] || usage

cp -v "${SUNVOX_LIB_DIR}/linux/lib_arm64/sunvox.so" linux/lib_arm64/
cp -v "${SUNVOX_LIB_DIR}/linux/lib_arm_armhf_raspberry_pi/sunvox.so" linux/lib_arm_armhf_raspberry_pi/
cp -v "${SUNVOX_LIB_DIR}/linux/lib_x86/sunvox.so" linux/lib_x86/
cp -v "${SUNVOX_LIB_DIR}/linux/lib_x86_64/sunvox.so" linux/lib_x86_64/
cp -v "${SUNVOX_LIB_DIR}/macos/lib_x86_64/sunvox.dylib" osx/lib_x86_64/
cp -v "${SUNVOX_LIB_DIR}/windows/lib_x86/sunvox.dll" windows/lib_x86/
cp -v "${SUNVOX_LIB_DIR}/windows/lib_x86_64/sunvox.dll" windows/lib_x86_64/
