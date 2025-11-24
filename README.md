# Pallectrum - Lightweight Palladium Wallet

```
Licence: MIT Licence
Version: 0.1.0
Maintainer: Davide Grilli
Language: Python (>= 3.10)
Homepage: https://github.com/palladium-coin/pallectrum
```

[![Licence](https://img.shields.io/badge/license-MIT-blue.svg)](LICENCE)
[![Based on Electrum](https://img.shields.io/badge/based%20on-Electrum%204.6.2-green.svg)](https://github.com/spesmilo/electrum)


## About

Pallectrum is a lightweight Palladium wallet based on [Electrum](https://electrum.org/), the popular Bitcoin wallet. It offers the same ease of use, security features, and extensibility that Electrum is known for, but adapted for the Palladium blockchain.

### Key Features

- **Instant on**: Your wallet is ready to use immediately - no blockchain download required
- **Secure**: Your private keys are encrypted and never leave your computer
- **Forgiving**: Your funds can be recovered from a secret seed phrase
- **Cold Storage**: Keep your private keys offline and transact using a watching-only wallet
- **Multi-signature support**: Split the permission to spend your coins between several wallets
- **Hardware wallet support**: Compatible with popular hardware wallets (Trezor, Ledger, etc.)
- **Lightning Network**: Fast and low-cost payments (experimental)

### Based on Electrum

Pallectrum is a fork of Electrum v4.6.2, adapted to work with the Palladium blockchain. For the original Electrum documentation, see [README-ELECTRUM.md](README-ELECTRUM.md).

**Credits**: Pallectrum is based on [Electrum](https://github.com/spesmilo/electrum) by Thomas Voegtlin and contributors. We are grateful for their excellent work.


## Getting Started

### Installation

The easiest way to run Pallectrum is to download the pre-built binaries:

- **Windows**: Download `pallectrum-x.x.x-setup.exe`
- **Linux**: Download `pallectrum-x.x.x-x86_64.AppImage`
- **Android**: Download `pallectrum-x.x.x.apk`

### Running from Source

If you want to run Pallectrum from source, you'll need Python 3.10 or higher.

#### Quick Start (Linux/macOS)

```bash
$ sudo apt-get install libsecp256k1-dev python3-pyqt6
$ git clone https://github.com/palladium-coin/pallectrum.git
$ cd pallectrum
$ python3 -m pip install --user -e .
$ ./run_electrum
```

For detailed installation instructions, including dependencies and platform-specific notes, see the [original Electrum documentation](README-ELECTRUM.md#getting-started).


## Building Binaries

Pallectrum includes Docker-based build systems for reproducible builds:

- **Windows**: See [contrib/build-wine/README.md](contrib/build-wine/README.md)
- **Linux (AppImage)**: See [contrib/build-linux/appimage/README.md](contrib/build-linux/appimage/README.md)
- **Android**: See [contrib/android/Readme.md](contrib/android/Readme.md)

### Quick Build (Windows with Docker)

```bash
$ cd contrib/build-wine
$ ./build.sh
# Output: dist/pallectrum-<version>-setup.exe
```


## Configuration

Pallectrum stores wallet data and configuration in:

- **Windows**: `C:\Users\<username>\AppData\Roaming\Pallectrum`
- **Linux/macOS**: `~/.pallectrum`
- **Android**: `<internal storage>/Pallectrum`


## Palladium-Specific Features

Pallectrum includes specific adaptations for the Palladium blockchain:

- BIP21 URI scheme: `palladium:` (instead of `bitcoin:`)
- BIP44 coin type: 746
- Default block explorer: https://explorer.palladium-coin.com/
- Currency unit: PLM (Palladium) instead of BTC
- Checkpoint-based validation (compatible with LWMA difficulty algorithm)


## Development

### Running Tests

```bash
$ pytest tests -v
```

### Project Structure

Pallectrum maintains the same structure as Electrum:

- `electrum/` - Core wallet library (note: directory name kept for compatibility)
- `contrib/` - Build scripts and utilities
- `tests/` - Unit and integration tests


## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues on GitHub.

For Pallectrum-specific issues:
- Repository: https://github.com/palladium-coin/pallectrum

For general Electrum-related questions:
- Original project: https://github.com/spesmilo/electrum


## Licence

Pallectrum is released under the terms of the MIT Licence. See [LICENCE](LICENCE) for more information.

This project is based on Electrum, which is also released under the MIT Licence.
Copyright (C) 2011-2024 Thomas Voegtlin and contributors


## Links

- **Palladium Explorer**: https://explorer.palladium-coin.com/
- **GitHub Repository**: https://github.com/palladium-coin/pallectrum
- **Original Electrum**: https://electrum.org/
- **Electrum Documentation**: [README-ELECTRUM.md](README-ELECTRUM.md)
