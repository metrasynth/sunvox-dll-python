#!/usr/bin/env bash
#
# Copies libs from the SunVox library distribution.

set -euo pipefail

usage() {
    echo "Usage: $0 <sunvox-library-dir>"
    exit 1
}

[[ "$*" != "" ]] || usage

SUNVOX_LIB_DIR="$1"

[[ -d "${SUNVOX_LIB_DIR}" ]] || usage

SUNVOX_LIB_SUBPATHS="
linux/lib_arm/
linux/lib_arm64/
linux/lib_x86/
linux/lib_x86_64/
macos/lib_arm64/
macos/lib_x86_64/
windows/lib_x86/
windows/lib_x86_64/
"

for REL_SUBPATH in ${SUNVOX_LIB_SUBPATHS}
do
    SRC_SUBPATH="${SUNVOX_LIB_DIR}/${REL_SUBPATH}"
    mkdir -p "${REL_SUBPATH}"
    cp -v "${SRC_SUBPATH}"sunvox.* "${REL_SUBPATH}"
done
