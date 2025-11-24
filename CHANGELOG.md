# Changelog

All notable changes to Pallectrum will be documented in this file.

**Pallectrum** is a lightweight wallet client for the Palladium blockchain.
It is based on Electrum Bitcoin Wallet, adapted to support Palladium's network
and consensus rules. Palladium is a Bitcoin fork with custom parameters and features.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Placeholder for future changes

---

## [0.1.0] - 2025-11-24

### Initial Fork Release

This is the initial fork of Electrum for the Palladium blockchain project.

**Fork Information:**
- **Forked from**: Electrum v4.6.2
- **Base commit**: [`d15598bcf034e21718e2cc1152c3ae965c5449df`](https://github.com/spesmilo/electrum/commit/d15598bcf034e21718e2cc1152c3ae965c5449df)
- **Original project**: [Electrum Bitcoin Wallet](https://github.com/spesmilo/electrum)
- **Fork date**: November 24, 2025
- **Fork maintainer**: Davide Grilli

### Added

#### Palladium Blockchain Integration
- **Palladium network parameters**
  - Genesis block configuration
  - Network magic bytes
  - Default network ports (mainnet: 2333, testnet: 12333)
  - Block time: 2 minutes (120 seconds)
  - BIP44 coin type: 746
- **Palladium address format support**
  - Bech32 address format (default)
  - Address validation for Palladium network
  - P2PKH, P2WPKH, P2SH-P2WPKH address types
- **Palladium Electrum server infrastructure**
  - Default server list for Palladium network:
    - 173.212.224.67:50002 (SSL) / 50001 (TCP)
    - 144.91.120.225:50002 (SSL) / 50001 (TCP)
    - 66.94.115.80:50002 (SSL) / 50001 (TCP)
    - 89.117.149.130:50002 (SSL) / 50001 (TCP)
  - Server discovery protocol adaptation
  - SSL/TCP protocol support (version 1.4.2)
- **Consensus algorithm integration**
  - LWMA (Lightweight Moving Average) difficulty adjustment from block 29000
  - Checkpoint-based validation system (161 checkpoints covering blocks 0-324,575)
  - Block reward schedule for Palladium
  - Coinbase maturity: 120 blocks

#### BIP Standards Implementation
- **BIP21 URI scheme**: `palladium:` (instead of `bitcoin:`)
  - Payment URI parsing and generation
  - QR code integration with palladium scheme
  - Amount and message parameter support
- **BIP44 derivation path**: m/44'/746'/0' (Palladium coin type)
- **Default address type**: Bech32 (p2wpkh) for WIF imports

#### User Interface & Branding
- **Complete rebranding from Electrum to Pallectrum**
  - Application name and window titles
  - Tray icon and notifications
  - About dialog and version information (0.1.0)
  - Documentation and help texts
  - Terms of Use dialog
- **Currency unit changes**
  - Base units: PLM, mPLM, bits, sat (instead of BTC, mBTC)
  - Default unit: mPLM (5 decimal places)
  - All GUI labels and input validators updated
  - Chart and graph labels (BTC → PLM)
  - Amount formatting and display
- **Block explorer integration**
  - Default explorer: https://explorer.palladium-coin.com/
  - Transaction, address, and block lookups
- **Network name display**
  - Shows "Palladium Mainnet" / "Palladium Testnet"
  - Updated in all GUI components (Qt, QML, text)

#### Build System
- **Docker-based reproducible builds**
  - Windows (Wine): Updated for Pallectrum branding
  - Linux AppImage: Updated for Pallectrum branding
  - Android APK: Updated for Pallectrum branding
  - All build paths changed from `electrum` to `pallectrum`
  - Docker image names updated (e.g., `pallectrum-wine-builder-img`)
- **Binary naming**
  - Windows: `pallectrum-VERSION-setup.exe`
  - Linux: `pallectrum-VERSION-x86_64.AppImage`
  - Android: `pallectrum-VERSION.apk`
- **Code signing**
  - NSIS installer signed as "Pallectrum"
  - Certificate setup for Windows binaries

#### Documentation
- **README.md**: Complete rewrite for Pallectrum
  - Getting Started guide
  - Installation instructions
  - Building from source
  - Palladium-specific features documentation
  - Credits to original Electrum project
- **README-ELECTRUM.md**: Original Electrum v4.6.2 documentation preserved
- **AUTHORS**: Added Davide Grilli as Pallectrum maintainer
- **CHANGELOG.md**: This file, tracking all fork changes

### Changed

#### Core Functionality
- **Network connection logic** adapted for Palladium blockchain
- **Transaction validation rules** for Palladium consensus
- **Fee estimation** adapted to Palladium network conditions
- **Wallet data directory**:
  - Windows: `C:\Users\<username>\AppData\Roaming\Pallectrum`
  - Linux/macOS: `~/.pallectrum`
  - Android: `<internal storage>/Pallectrum`

#### GUI Updates
- **Android (QML) GUI**
  - Fixed all hardcoded "BTC" and "Bitcoin" references
  - Updated wallet wizard and preferences
  - Fixed QR code scanning (removed hardcoded BTC unit)
  - Updated derivation paths (coin type 0 → 746)
  - Network connection dialogs show Palladium
- **Qt (Desktop) GUI**
  - Application name in all dialogs
  - Notification messages
  - Export/import dialogs
  - Hardware wallet integration screens
  - Settings and preferences panels
- **Text GUI**
  - Command-line help text
  - Daemon mode messages
  - Error messages and prompts

#### Build Configuration
- **setup.py**: Package name, description, author updated
- **buildozer_qml.spec**: Android package domain `org.palladium.pallectrum`
- **electrum.desktop**: Linux desktop entry for Pallectrum
- **electrum.nsi**: Windows installer for Pallectrum
- **All contrib build scripts**: Updated paths and names

### Fixed

#### Critical Fixes
- **Android QML GUI crashes**
  - Fixed QR code scanning crash (hardcoded "BTC" reference)
  - Fixed wallet creation with incorrect derivation paths
  - Fixed BIP21 URI parsing for palladium scheme
- **Address generation**
  - WIF import now defaults to bech32 (p2wpkh)
  - Correct derivation paths for Palladium (BIP44 coin type 746)
- **Checkpoint validation**
  - LWMA difficulty algorithm incompatibility resolved
  - Checkpoint-based validation ensures chain security
  - Skips PoW validation for checkpointed blocks

#### UI/UX Fixes
- **Balance display**: Correct formatting with PLM units
- **Amount input**: Regex validators accept PLM notation
- **QR codes**: Generate correct palladium: URIs
- **Network status**: Shows "Palladium" instead of "Bitcoin"
- **Update check**: Disabled automatic update prompts on startup

### Security
- Checkpoint-based validation provides security for blocks with LWMA difficulty
- 161 checkpoints covering blocks 0 through 324,575
- Will merge relevant security fixes from Electrum upstream as needed

### Removed
- Bitcoin-specific features incompatible with Palladium
- References to bitcoin.org and electrum.org in user-facing text
- Automatic update checking (to avoid confusion with Electrum updates)

---

## Upstream Synchronization

This fork is based on Electrum and may periodically merge upstream changes for:
- **Security fixes**: Critical vulnerabilities will be merged immediately
- **Bug fixes**: Important bug fixes affecting wallet functionality
- **Performance improvements**: Optimizations that benefit Pallectrum users

**Note**: Breaking changes or Bitcoin-specific features from upstream will be evaluated
case-by-case for compatibility with Palladium blockchain.

**Upstream repository**: https://github.com/spesmilo/electrum
**Upstream releases**: https://github.com/spesmilo/electrum/releases

### Upstream Merge History

| Pallectrum Version | Based on Electrum | Upstream Commit | Merge Date | Notes |
|-------------------|-------------------|-----------------|------------|-------|
| 0.1.0 | 4.6.2 | [d15598b](https://github.com/spesmilo/electrum/commit/d15598bcf034e21718e2cc1152c3ae965c5449df) | 2025-11-24 | Initial fork |

---

## Contributing

Contributions to Pallectrum are welcome! For contributing guidelines, please refer
to the main README.

For understanding upstream Electrum changes:
- [Electrum Release Notes](https://github.com/spesmilo/electrum/blob/master/RELEASE-NOTES)
- [Electrum Contributing Guide](https://github.com/spesmilo/electrum/blob/master/CONTRIBUTING.md)

---

## Links

- **Pallectrum Repository**: https://github.com/palladium-coin/pallectrum
- **Palladium Explorer**: https://explorer.palladium-coin.com/
- **Issue Tracker**: https://github.com/palladium-coin/pallectrum/issues

### Upstream Project Links
- **Electrum Website**: https://electrum.org/
- **Electrum GitHub**: https://github.com/spesmilo/electrum
- **Electrum Documentation**: https://electrum.readthedocs.io/

---

## Version Comparison Links

- [Unreleased changes](../../compare/v0.1.0...HEAD)
- [0.1.0 Release](../../releases/tag/v0.1.0)

---

**Last Updated**: 2025-11-24
**Maintained by**: Davide Grilli
