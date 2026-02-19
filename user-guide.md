# Pallectrum User Guide

Welcome to the Pallectrum user guide. This document will help you understand and use Pallectrum, the lightweight wallet for the Palladium blockchain.

---

## Table of Contents

1. [What is Pallectrum?](#1-what-is-pallectrum)
2. [How Pallectrum Works](#2-how-pallectrum-works)
3. [Creating a New Wallet](#3-creating-a-new-wallet)
4. [Backing Up Your Seed Phrase](#4-backing-up-your-seed-phrase)
5. [Recovering a Wallet from Seed](#5-recovering-a-wallet-from-seed)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. What is Pallectrum?

Pallectrum is a lightweight wallet application for the Palladium blockchain, based on the popular Electrum Bitcoin wallet. It provides a secure and user-friendly way to manage your Palladium (PLM) coins without downloading the entire blockchain.

**Key Features:**
- **Instant startup**: No blockchain download required
- **Secure**: Private keys are encrypted and never leave your computer
- **Forgiving**: Your funds can be recovered from a secret seed phrase
- **Cross-platform**: Available for Windows, Linux and Android

---

## 2. How Pallectrum Works

Pallectrum uses the **SPV (Simplified Payment Verification)** model, which means it connects to remote Electrum-style servers to retrieve blockchain data without storing the entire chain locally.

**Architecture:**
- **Lightweight client**: Connects to Palladium Electrum servers
- **SPV verification**: Verifies transactions using block headers only
- **No full node required**: Your wallet is ready to use immediately
- **Privacy-focused**: Your private keys never leave your device

**Technical Details:**
- BIP44 coin type: 746 (Palladium-specific)
- Address types:
  - **Bech32 SegWit (Strongly Recommended)**: Native SegWit addresses with `plm` prefix - most supported in Palladium network, lowest fees, best efficiency
  - P2PKH (Legacy): Addresses start with 'P' - basic support
  - P2SH: Addresses start with '3' - basic support
- Network: Connects to multiple servers for redundancy

---

## 3. Creating a New Wallet

Creating a new wallet in Pallectrum is a straightforward process that generates a secure seed phrase for you.

**Steps to create a new wallet:**
1. Launch Pallectrum application
2. Select "Create new wallet" from the wallet wizard
3. Choose your wallet type:
   - **Standard** (Recommended - fully tested)
   - Multi-signature (experimental)
   - Hardware wallet (experimental)
   - **Import addresses or private keys** (fully tested)
4. For a Standard wallet, choose how to create it:
   - **Create a new seed**: Generate a new 12-word seed phrase (recommended for new wallets)
   - **I already have a seed**: Restore from an existing seed phrase
   - **Use a master key**: Import using a master private/public key
   - **Use a hardware device** (experimental - not tested)
5. If creating a new seed, the application will generate a 12-word seed phrase
6. Write down your seed phrase and store it safely
7. Confirm your seed phrase by entering it again
8. Set a password to encrypt your wallet file (recommended)
9. Your wallet is ready to use

**Important:**
- Your seed phrase is the master key to your funds
- Never share your seed phrase with anyone
- Store it in a secure, offline location
- **Use Standard wallet type** for production use (other types are not fully tested yet)

### Advanced Wallet Creation Options

#### Extending Seed Phrase with Custom Words (Passphrase)

When creating or restoring a wallet from seed, you can optionally extend your seed phrase with custom words (also called a "passphrase" or "salt"):

**How it works:**
- After entering your 12-word seed phrase, you can add additional custom words
- These custom words are combined with your seed using PBKDF2-HMAC-SHA512 (2048 rounds)
- Each different passphrase creates a completely different wallet
- The passphrase is NOT part of the BIP39 standard seed words

**Use cases:**
- **Enhanced security**: Even if someone finds your 12-word seed, they cannot access funds without the passphrase
- **Plausible deniability**: Create multiple wallets from the same seed with different passphrases (e.g., one with small amounts, one with larger amounts)
- **Two-factor security**: Seed phrase (something you have) + passphrase (something you know)

**Critical warnings:**
- If you forget your passphrase, your funds are **permanently lost** - there is no recovery mechanism
- Write down your passphrase separately from your seed phrase
- Test wallet recovery with both seed AND passphrase before depositing funds
- The passphrase is case-sensitive and spaces matter

#### Using a Master Key

A **master key** is the root cryptographic key from which all your wallet addresses are derived. Pallectrum allows you to import a wallet using a master key instead of a seed phrase.

**What is a master key?**
- A master key is a long hexadecimal string (extended private or public key)
- Format: starts with `xprv` (private) or `xpub` (public) for mainnet
- Derived from your seed phrase using BIP32 hierarchical deterministic key derivation
- Contains both the key material and chain code for generating child keys

**Types of master keys:**

Master keys come in different formats depending on the address type they generate:

1. **Standard (Legacy) Keys - P2PKH addresses**
   - **xprv** (private) / **xpub** (public) - mainnet
   - **tprv** (private) / **tpub** (public) - testnet
   - Generates legacy P2PKH addresses (starting with 'P' in Palladium)
   - Most compatible format, supported by all wallets

2. **SegWit Wrapped Keys - P2WPKH-P2SH addresses**
   - **yprv** (private) / **ypub** (public) - mainnet
   - **uprv** (private) / **upub** (public) - testnet
   - Generates SegWit addresses wrapped in P2SH (starting with '3')

3. **Native SegWit Keys - P2WPKH addresses (Bech32)**
   - **zprv** (private) / **zpub** (public) - mainnet
   - **vprv** (private) / **vpub** (public) - testnet
   - Generates native SegWit Bech32 addresses (starting with 'plm')
   - **Strongly Recommended**: Most supported in Palladium network
   - Lowest fees and best efficiency

**Private vs Public Keys:**
- **Private keys** (xprv, yprv, zprv):
  - Can generate both addresses and private keys (full wallet control)
  - Allows spending funds
  - Should be kept secure like a seed phrase

- **Public keys** (xpub, ypub, zpub):
  - Can only generate addresses, not private keys
  - Creates a "watch-only" wallet (can see balance but cannot spend)
  - Safe to share for monitoring purposes

**When to use master keys:**
- **Cold storage setup**: Use xpub on online device (watch-only), keep xprv offline
- **Business accounting**: Share xpub with accountants to monitor transactions without spending ability
- **Advanced key management**: Import keys from other BIP32-compatible wallets
- **Hardware wallet coordination**: Some advanced users coordinate between devices

**Security considerations:**
- Master private key (xprv) = same security level as seed phrase
- Master public key (xpub) reveals all your addresses and transaction history
- Never share your xprv with anyone
- Be cautious sharing xpub as it reduces privacy

**Example format:**
```
xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi
xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8
```

---

## 4. Backing Up Your Seed Phrase

Your seed phrase is the most critical backup of your wallet. Pallectrum uses industry-standard cryptographic methods to derive your keys from the seed.

### Seed Phrase Basics
- **12 words**: Your seed is a sequence of words from the BIP39 wordlist
- **Deterministic**: The same seed always generates the same wallet
- **Portable**: Can be used to restore your wallet on any device

### Encryption and Passphrase (Salt)

Pallectrum supports an **optional passphrase** (also called "salt" or "extension word") for additional security:

**How it works:**
- The passphrase is combined with your seed phrase during key derivation
- Uses **PBKDF2-HMAC-SHA512** with 2048 rounds
- Salt format: `electrum` + your passphrase
- Creates a completely different wallet for each passphrase

**Benefits of using a passphrase:**
- **Plausible deniability**: Different passphrases create different wallets
- **Additional security layer**: Even if someone finds your seed, they need the passphrase
- **Two-factor security**: "Something you have" (seed) + "Something you know" (passphrase)

**Important warnings:**
- If you forget your passphrase, your funds are **permanently lost**
- Write down both your seed phrase AND passphrase separately
- Test your backup by restoring it before depositing large amounts
- Store seed and passphrase in different secure locations

### Wallet File Encryption

In addition to the optional passphrase, Pallectrum encrypts your wallet file with a password:
- Protects your wallet data on disk
- Required every time you open the wallet
- Does NOT affect seed phrase recovery
- Can be changed from the wallet settings

---

## 5. Recovering a Wallet from Seed

If you need to restore your wallet (new device, lost wallet file, etc.), you can recover it using your seed phrase.

**Steps to recover a wallet:**

1. Launch Pallectrum application
2. Select "I already have a seed" in the wallet wizard
3. Enter your seed phrase (12 words)
4. If you used a passphrase, enter it when prompted
5. Choose wallet type and address type (use "Standard" if unsure)
6. Set a new password for the wallet file
7. Wait for the wallet to synchronize and scan for transactions
8. Your funds and transaction history will appear

**Recovery Options:**
- **Standard recovery**: Enter your seed phrase to restore your wallet
- **With passphrase**: Include your passphrase if you used one during creation
- **BIP39 compatibility**: Pallectrum supports standard BIP39 seeds
- **Multi-language**: Seeds can be entered in English, Spanish, Japanese, Portuguese, or Chinese

**Troubleshooting:**
- **No funds visible**: Ensure you entered the correct passphrase (if used)
- **Wrong wallet type**: Try different address types (P2PKH, P2SH, SegWit)
- **Synchronization issues**: Check your network connection and server status
- **Invalid seed**: Verify you copied all words correctly and in the right order

**Best practices:**
- Test your seed phrase recovery shortly after creating the wallet
- Verify the first receiving address matches your original wallet
- Never enter your seed phrase on untrusted devices or websites
- Use the official Pallectrum application from trusted sources only

---

## 6. Troubleshooting

### Cannot Connect to Server — SSL Certificate Error

#### Why this happens

When Pallectrum connects to an Electrum server for the first time, it downloads and saves the server's SSL/TLS certificate locally. On subsequent connections, it compares the stored certificate with the one the server presents. If they do not match, the connection is refused — this is a security mechanism to protect you against man-in-the-middle attacks.

This becomes a problem with **self-signed certificates**, which are common on personal or community-run servers. Unlike certificates issued by a trusted authority (CA), self-signed certificates are generated directly by the server administrator. They provide encryption, but they are not verified by any third party. When the administrator renews or replaces the certificate (for example, after it expires or following server maintenance), the new certificate no longer matches the one Pallectrum has stored locally, and the connection fails silently.

**In short:** Pallectrum remembers "this server uses this exact certificate." If the certificate changes — even legitimately — Pallectrum refuses to reconnect until the old cached certificate is deleted.

#### Symptoms

- The wallet stays disconnected after selecting a personal or custom server
- The status bar shows no connection even though the server is online
- The problem started after a server update or maintenance window

#### Solution

Delete the locally cached certificate so that Pallectrum can fetch and store the new one on the next connection attempt.

**On Android / QML interface:**

1. Open the app and go to **Network** (bottom navigation bar)
2. Tap **Server Settings**
3. Tap the reset icon (🗑) next to the server address field
4. Select **SSL certificates**
5. Confirm when prompted
6. The app will reconnect automatically and store the new certificate

**On Desktop (Windows / Linux):**

1. Open the **Tools** menu → **Network**
2. Go to the **Server** tab
3. Click **Reset SSL certificates**
4. Confirm when prompted

After resetting, Pallectrum will reconnect to the server and cache the new certificate. If the connection still fails, verify that the server address is correct and that the server is online.
