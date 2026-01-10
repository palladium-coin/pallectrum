#!/bin/bash

set -e

APPDIR="$(dirname "$(readlink -e "$0")")"

# Detect architecture-specific lib directory
if [ -d "${APPDIR}/usr/lib/x86_64-linux-gnu" ]; then
    ARCH_LIB_DIR="x86_64-linux-gnu"
elif [ -d "${APPDIR}/usr/lib/aarch64-linux-gnu" ]; then
    ARCH_LIB_DIR="aarch64-linux-gnu"
else
    # Fallback to x86_64 for backward compatibility
    ARCH_LIB_DIR="x86_64-linux-gnu"
fi

export LD_LIBRARY_PATH="${APPDIR}/usr/lib/:${APPDIR}/usr/lib/${ARCH_LIB_DIR}${LD_LIBRARY_PATH+:$LD_LIBRARY_PATH}"
export PATH="${APPDIR}/usr/bin:${PATH}"
export LDFLAGS="-L${APPDIR}/usr/lib/${ARCH_LIB_DIR} -L${APPDIR}/usr/lib"

exec "${APPDIR}/usr/bin/python3" -s "${APPDIR}/usr/bin/electrum" "$@"
