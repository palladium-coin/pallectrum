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
- Palladium blockchain network parameters
  - Genesis block configuration
  - Network magic bytes
  - Default network ports (mainnet, testnet)
  - Block time and difficulty adjustment parameters
- Palladium address format support
  - Bech32 address format
  - Address validation for Palladium network
- Palladium Electrum server infrastructure
  - Default server list for Palladium network
  - Server discovery protocol adaptation
  - SSL certificate handling for Palladium servers
- Consensus algorithm integration
  - Difficulty retargeting algorithm
  - Block reward schedule for Palladium

### Changed
- Rebranding from Electrum to Pallectrum
  - Application name and window titles
  - Icon set and visual identity
  - About dialog and version information
  - Documentation and help texts
- Network connection logic to support Palladium blockchain
- Transaction validation rules for Palladium consensus
- Fee estimation adapted to Palladium network conditions

### Fixed
- **Android (QML) GUI critical fixes**
  - Fixed QR code scanning crash due to hardcoded "BTC" unit reference
  - Fixed hardcoded Bitcoin derivation paths (coin type 0 → 746 for Palladium)
  - Fixed BIP21 URI scheme (bitcoin → palladium)
  - Fixed QR code URL encoding to use palladium scheme
- **Complete Android/QML rebranding**
  - Updated all user-visible "Electrum" references to "Pallectrum"
  - Fixed network name display (shows "Palladium Mainnet" instead of "Mainnet")
  - Updated wallet wizard, preferences, error dialogs, and help texts
  - Fixed "Import Bitcoin addresses" to "Import Palladium addresses"
- **Qt (Desktop) GUI rebranding**
  - Updated application name, tray tooltip, and exit menu
  - Fixed notification branding
  - Updated chart labels (BTC → PLM)
- **Balance unit display**
  - Fixed amount regex validator to use PLM instead of BTC
  - Updated preferences text for thousands separators

### Security
- Will merge relevant security fixes from Electrum upstream as needed

---

## [0.1.0] - 2025-11-20

### Initial Fork Release

This is the initial fork of Electrum for the Palladium blockchain project.

**Fork Information:**
- **Forked from**: Electrum v4.6.2
- **Base commit**: [`d15598bcf034e21718e2cc1152c3ae965c5449df`](https://github.com/spesmilo/electrum/commit/d15598bcf034e21718e2cc1152c3ae965c5449df)
- **Original project**: [Electrum Bitcoin Wallet](https://github.com/spesmilo/electrum)
- **Fork date**: November 20, 2025
- **Fork maintainer**: Davide Grilli

### Added
- Initial fork of Electrum 4.6.2 codebase
- Pallectrum copyright and license information
- This CHANGELOG.md to document all modifications from upstream

### Changed
- Updated `LICENCE` file with Pallectrum fork copyright
  - Added: Copyright (C) 2025 Davide Grilli - Pallectrum Fork
  - Maintained: Full attribution to Electrum developers and Thomas Voegtlin
  - License: MIT License (preserved from upstream)

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
| 0.1.0 | 4.6.2 | [d15598b](https://github.com/spesmilo/electrum/commit/d15598bcf034e21718e2cc1152c3ae965c5449df) | 2025-11-20 | Initial fork |

---

## Development Roadmap

### Phase 1: Core Blockchain Integration (v0.2.0)
- [ ] Implement Palladium network parameters
- [ ] Add Palladium address format support
- [ ] Configure Palladium Electrum servers
- [ ] Test blockchain synchronization

### Phase 2: UI/UX Customization (v0.3.0)
- [ ] Complete rebranding to Pallectrum
- [ ] Update icons and visual assets
- [ ] Localize help texts and documentation
- [ ] Test user workflows

### Phase 3: Production Release (v1.0.0)
- [ ] Security audit
- [ ] Performance optimization
- [ ] Comprehensive testing (mainnet & testnet)
- [ ] Build distribution packages (Windows, macOS, Linux, Android)

---

## Contributing

Contributions to Pallectrum are welcome! For contributing guidelines, please refer
to the main README.

For understanding upstream Electrum changes:
- [Electrum Release Notes](https://github.com/spesmilo/electrum/blob/master/RELEASE-NOTES)
- [Electrum Contributing Guide](https://github.com/spesmilo/electrum/blob/master/CONTRIBUTING.md)

---

## Links

- **Pallectrum Repository**: https://github.com/yourusername/pallectrum _(update with actual URL)_
- **Palladium Blockchain**: _(add Palladium project URL)_
- **Issue Tracker**: _(add issue tracker URL)_
- **Documentation**: _(add docs URL when available)_

### Upstream Project Links
- **Electrum Website**: https://electrum.org/
- **Electrum GitHub**: https://github.com/spesmilo/electrum
- **Electrum Documentation**: https://electrum.readthedocs.io/

---

## Version Comparison Links

- [Unreleased changes](../../compare/v0.1.0...HEAD)
- [0.1.0 Release](../../releases/tag/v0.1.0)

---

**Last Updated**: 2025-11-23
**Maintained by**: Davide Grilli
