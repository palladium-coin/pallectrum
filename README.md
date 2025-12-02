# Pallectrum - Lightweight Palladium Wallet

```
Licence: MIT Licence
Version: 0.2.0
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

#### Windows

**Prerequisites:**

- Python 3.10+ installed from [python.org](https://www.python.org/downloads/)

**Setup with Virtual Environment:**

```powershell
# Clone repository
git clone https://github.com/palladium-coin/pallectrum.git
cd pallectrum

# Create and activate virtual environment
python -m venv env
env\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -e ".[gui,crypto]"

# Copy libsecp256k1 DLL (if needed)
copy libsecp256k1*.dll env\Lib\site-packages\electrum_ecc\

# Run with Qt GUI
python run_electrum
```

##### Optional: QML GUI on Windows (simulates Android interface)

```powershell
pip install ".[qml_gui]"
python run_electrum gui -g qml
```

#### Linux (Ubuntu/Debian)

**Install Prerequisites:**

```bash
# System packages
sudo apt update
sudo apt install -y python3-venv python3-pip build-essential python3-dev
sudo apt install -y libffi-dev libssl-dev libsecp256k1-dev
```

**Setup with Virtual Environment:**

```bash
# Clone repository
git clone https://github.com/palladium-coin/pallectrum.git
cd pallectrum

# Create and activate virtual environment
python3 -m venv env
source env/bin/activate

# Upgrade pip and install dependencies
python3 -m pip install --upgrade pip
pip install -e ".[gui,crypto]"

# Run with Qt GUI
python run_electrum
```

##### Optional: QML GUI on Linux (simulates Android interface)

```bash
pip install ".[qml_gui]"
python run_electrum gui -g qml
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
