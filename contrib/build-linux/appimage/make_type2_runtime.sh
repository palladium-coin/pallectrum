#!/bin/bash

set -e

PROJECT_ROOT="$(dirname "$(readlink -e "$0")")/../../.."
PROJECT_ROOT_OR_FRESHCLONE_ROOT="$PROJECT_ROOT"
CONTRIB="$PROJECT_ROOT/contrib"
CONTRIB_APPIMAGE="$CONTRIB/build-linux/appimage"

# when bumping the runtime commit also check if the `type2-runtime-reproducible-build.patch` still works
TYPE2_RUNTIME_COMMIT="5e7217b7cfeecee1491c2d251e355c3cf8ba6e4d"
TYPE2_RUNTIME_REPO="https://github.com/AppImage/type2-runtime.git"

. "$CONTRIB"/build_tools_util.sh

# Determine architecture (default to x86_64 if not set)
ARCH="${ARCH:-x86_64}"
if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "aarch64" ]; then
    fail "Unsupported ARCH: $ARCH. Must be x86_64 or aarch64"
fi
info "Building type2-runtime for architecture: $ARCH"

# Use a shared cache location that persists across fresh clones
# This is critical for reproducible builds with ELECBUILD_COMMIT
TYPE2_RUNTIME_REPO_DIR="$PROJECT_ROOT/contrib/build-linux/appimage/.cache/appimage/type2-runtime"
if [ -f "$TYPE2_RUNTIME_REPO_DIR/runtime-$ARCH" ] && [ -s "$TYPE2_RUNTIME_REPO_DIR/runtime-$ARCH" ]; then
    info "type2-runtime already built ($(du -h "$TYPE2_RUNTIME_REPO_DIR/runtime-$ARCH" | cut -f1)), skipping"
    exit 0
fi

# If directory exists but runtime is missing or invalid, clean it up
if [ -d "$TYPE2_RUNTIME_REPO_DIR" ]; then
    warn "type2-runtime directory exists but runtime is missing or invalid, cleaning up..."
    rm -rf "$TYPE2_RUNTIME_REPO_DIR"
fi

clone_or_update_repo "$TYPE2_RUNTIME_REPO" "$TYPE2_RUNTIME_COMMIT" "$TYPE2_RUNTIME_REPO_DIR"

# Apply patch to make runtime build reproducible
info "Applying type2-runtime patch..."
cd "$TYPE2_RUNTIME_REPO_DIR"
# Check if patch can be applied (it will fail if already applied or incompatible)
if git apply --check "$CONTRIB_APPIMAGE/patches/type2-runtime-reproducible-build.patch" >/dev/null 2>&1; then
    git apply "$CONTRIB_APPIMAGE/patches/type2-runtime-reproducible-build.patch" || fail "Failed to apply runtime repo patch"
else
    warn "Patch already applied or cannot be applied, continuing..."
fi

info "building type2-runtime in build container..."
cd "$TYPE2_RUNTIME_REPO_DIR/scripts/docker"
env ARCH="$ARCH" ./build-with-docker.sh || fail "Failed to build type2-runtime with docker"

# Verify the runtime was created in the expected location
if [ ! -f "./runtime-$ARCH" ]; then
    fail "Runtime binary was not created by docker build (expected at: $TYPE2_RUNTIME_REPO_DIR/scripts/docker/runtime-$ARCH)"
fi

mv "./runtime-$ARCH" "$TYPE2_RUNTIME_REPO_DIR/"

# Verify runtime is valid (not empty)
if [ ! -s "$TYPE2_RUNTIME_REPO_DIR/runtime-$ARCH" ]; then
    fail "Runtime binary is empty or invalid"
fi

# clean up the empty created 'out' dir to prevent permission issues
rm -rf "$TYPE2_RUNTIME_REPO_DIR/out"

info "runtime build successful: $(sha256sum "$TYPE2_RUNTIME_REPO_DIR/runtime-$ARCH")"
