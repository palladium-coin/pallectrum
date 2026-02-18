# Pallectrum - Lightweight Palladium Wallet

```
Licence: MIT Licence
Version: 1.0.1
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

- **Windows**: Two versions available:
  - `pallectrum-x.x.x-portable.exe` - **Recommended for USB drives**. Saves all data (wallets, configuration) in the same directory as the executable. Perfect for portable installations.
  - `pallectrum-x.x.x-setup.exe` - Standalone installer. Installs to Program Files and saves data in `%APPDATA%\Pallectrum`.
- **Linux**: Two versions available:
  - `pallectrum-x.x.x-x86_64.AppImage` - For Intel/AMD 64-bit systems
  - `pallectrum-x.x.x-aarch64.AppImage` - For ARM64 systems
- **Android**: Download `pallectrum-x.x.x.apk`

### Running from Source

Running from source requires **Python 3.10 or higher**. Follow the steps for your platform below.

---

#### Windows

**Prerequisite:** Python 3.10+ from [python.org](https://www.python.org/downloads/)

```powershell
# Clone the repository
git clone https://github.com/palladium-coin/pallectrum.git
cd pallectrum

# Create and activate a virtual environment
python -m venv env
env\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
pip install -e ".[gui,crypto]"

# Copy the secp256k1 library (required on Windows)
copy libsecp256k1*.dll env\Lib\site-packages\electrum_ecc\

# Launch
python run_electrum
```

> **Optional – QML GUI** (simulates the Android interface):
> ```powershell
> pip install -e ".[qml_gui]"
> python run_electrum -g qml
> ```

---

#### Linux (Ubuntu / Debian)

##### 1. Install system prerequisites

```bash
sudo apt update
sudo apt install -y \
  python3-venv python3-pip python3-dev build-essential \
  libffi-dev libssl-dev libsecp256k1-dev libpulse0
```

##### 2. Clone the repository and set up the virtual environment

```bash
git clone https://github.com/palladium-coin/pallectrum.git
cd pallectrum

python3 -m venv env
source env/bin/activate
python3 -m pip install --upgrade pip
```

##### 3. Install dependencies

###### 3.1. x86_64 (Intel / AMD)

```bash
pip install -e ".[gui,crypto]"
```

###### 3.2. ARM64 / aarch64

> PyQt6 ≥ 6.9 wheels are not published for ARM64 on PyPI — pinned versions must be used.

```bash
pip install -r contrib/requirements/requirements.txt
pip install "cryptography>=2.6"
pip install --only-binary PyQt6,PyQt6-Qt6,PyQt6-sip \
  "PyQt6>=6.7.0,<6.8.0" \
  "PyQt6-Qt6>=6.7.0,<6.8.0" \
  "PyQt6-sip==13.10.2"
pip install -e .
```

##### 4. Launch

```bash
python run_electrum
```

###### 4.1. Optional – QML GUI (Android-like interface)

*x86_64*
```bash
pip install -e ".[qml_gui]"
python run_electrum -g qml
```

*ARM64* — the pinned PyQt6 packages installed in step 3 already include QML support:
```bash
python run_electrum -g qml
```

---

For the full list of dependencies and advanced configuration options, see [README-ELECTRUM.md#getting-started](README-ELECTRUM.md#getting-started).

## User Guide

For a comprehensive guide on how to use Pallectrum, including wallet creation, sending/receiving transactions, backup procedures, and advanced features, please refer to the **[User Guide](user-guide.md)**.

The guide covers:
- Creating and restoring wallets
- Sending and receiving Palladium
- Wallet backup and security best practices
- Advanced features (multi-signature, hardware wallets, etc.)
- Troubleshooting common issues


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

- BIP21 URI scheme: `palladium:`
- BIP44 coin type: 746
- Default block explorer: https://explorer.palladium-coin.com/
- Currency unit: PLM (Palladium)
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

### Development Notes

Development of Pallectrum was supported by **Claude 4.5 Sonnet** (Anthropic AI) for code analysis, debugging, refactoring, and documentation assistance.


## Licence

Pallectrum is released under the terms of the MIT Licence. See [LICENCE](LICENCE) for more information.

This project is based on Electrum, which is also released under the MIT Licence.
Copyright (C) 2011-2024 Thomas Voegtlin and contributors


## Links

- **Palladium Explorer**: https://explorer.palladium-coin.com/
- **GitHub Repository**: https://github.com/palladium-coin/pallectrum
- **Original Electrum**: https://electrum.org/
- **Electrum Documentation**: [README-ELECTRUM.md](README-ELECTRUM.md)
