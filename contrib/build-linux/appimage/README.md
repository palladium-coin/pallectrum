AppImage binary for Electrum
============================

✓ _This binary should be reproducible, meaning you should be able to generate
   binaries that match the official releases._

- _Minimum supported target system (i.e. what end-users need):_
  - _x86_64: glibc 2.31_
  - _aarch64 (ARM64): glibc 2.31_

This assumes an Ubuntu (or similar Debian-based) host, but it should not be too hard
to adapt to another similar system.

We support building AppImages for both x86_64 (amd64) and aarch64 (ARM64) architectures.
**Important**: The host architecture must match the target architecture (i.e., build
x86_64 AppImages on x86_64 hosts, and aarch64 AppImages on aarch64 hosts like Raspberry Pi).


1. Install Docker

    See [`contrib/docker_notes.md`](../../docker_notes.md).

    (worth reading even if you already have docker)

2. Build binary

    **For x86_64 (amd64):**
    ```
    $ ./build.sh
    ```
    Or for reproducibility:
    ```
    $ ELECBUILD_COMMIT=HEAD ./build.sh
    ```

    **For aarch64 (ARM64):**
    ```
    $ ARCH=aarch64 ./build.sh
    ```
    Or for reproducibility:
    ```
    $ ARCH=aarch64 ELECBUILD_COMMIT=HEAD ./build.sh
    ```

    **Note**: By default, `ARCH` is set to `x86_64` if not specified.

3. The generated binary is in `./dist`.

    Output files are named with the architecture suffix:
    - `pallectrum-<version>-x86_64.AppImage`
    - `pallectrum-<version>-aarch64.AppImage`


## FAQ

### How can I see what is included in the AppImage?
Execute the binary as follows: `./pallectrum*.AppImage --appimage-extract`

### How to investigate diff between binaries if reproducibility fails?
```
cd dist/
./pallectrum-*-x86_64.AppImage1 --appimage-extract
mv squashfs-root/ squashfs-root1/
./pallectrum-*-x86_64.AppImage2 --appimage-extract
mv squashfs-root/ squashfs-root2/
$(cd squashfs-root1; find -type f -exec sha256sum '{}' \; > ./../sha256sum1)
$(cd squashfs-root2; find -type f -exec sha256sum '{}' \; > ./../sha256sum2)
diff sha256sum1 sha256sum2 > d
cat d
```

(Replace `x86_64` with `aarch64` for ARM64 builds)

For file metadata, e.g. timestamps:
```
rsync -n -a -i --delete squashfs-root1/ squashfs-root2/
```

Useful binary comparison tools:
- vbindiff
- diffoscope
