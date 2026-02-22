"""
Tests for P2TR (Pay-to-Taproot) support on the Palladium network.
Covers:
  - Address generation (plm1p... bech32m format)
  - is_taproot_address() detection
  - BIP-86 derivation path recognition
  - pubkey_to_address() for script type 'p2tr'
  - xpub/xprv round-trip for p2tr keystore type
  - P2TR transaction signing (keypath spending)
  - TRDescriptor with 33-byte compressed pubkeys
"""

import copy
import os

import electrum_ecc as ecc
from electrum_ecc.util import bip340_tagged_hash

from electrum import bitcoin, constants, segwit_addr
from electrum.bitcoin import (
    taproot_output_script, taproot_tweak_pubkey, taproot_tweak_seckey,
    is_taproot_address, script_to_address,
    construct_witness,
)
from electrum.bip32 import BIP32Node, xpub_type
from electrum.keystore import xtype_from_derivation
from electrum.transaction import (
    PartialTransaction, PartialTxInput, PartialTxOutput, TxOutpoint, TxOutput, Sighash,
)
from electrum.descriptor import get_singlesig_descriptor_from_legacy_leaf, TRDescriptor
from electrum.util import bfh

from . import ElectrumTestCase


# Chiave privata deterministica per i test (scalar = 42)
_TEST_SECRET_SCALAR = 42


def _make_internal_keypair():
    """Restituisce (privkey_bytes_32, internal_pubkey_bytes_32) per i test."""
    privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
    privkey_bytes = privkey.get_secret_bytes()
    # internal pubkey: x-only (32 byte), strip prefix byte
    internal_pubkey = privkey.get_public_key_bytes(compressed=True)[1:]
    return privkey_bytes, internal_pubkey


class TestP2TRAddressGeneration(ElectrumTestCase):
    """Test generazione indirizzi P2TR Palladium (plm1p...)."""

    def test_p2tr_address_starts_with_plm1p(self):
        """Un indirizzo P2TR su Palladium inizia con 'plm1p'."""
        _, internal_pubkey = _make_internal_keypair()
        output_script = taproot_output_script(internal_pubkey, script_tree=None)
        addr = script_to_address(output_script)
        self.assertTrue(addr.startswith("plm1p"), f"Expected plm1p... got: {addr!r}")

    def test_p2tr_address_bech32m_decodes_correctly(self):
        """L'indirizzo P2TR decodifica con witness version 1 e programma da 32 byte."""
        _, internal_pubkey = _make_internal_keypair()
        output_script = taproot_output_script(internal_pubkey, script_tree=None)
        addr = script_to_address(output_script)
        witver, witprog = segwit_addr.decode_segwit_address(constants.net.SEGWIT_HRP, addr)
        self.assertEqual(witver, 1, "witness version deve essere 1 per P2TR")
        self.assertEqual(len(witprog), 32, "witness program deve essere 32 byte per P2TR")

    def test_p2tr_address_encodes_tweaked_pubkey(self):
        """Il witness program corrisponde alla chiave tweaked (BIP-341)."""
        _, internal_pubkey = _make_internal_keypair()
        _, tweaked_pubkey = taproot_tweak_pubkey(internal_pubkey, b"")
        output_script = taproot_output_script(internal_pubkey, script_tree=None)
        addr = script_to_address(output_script)
        _, witprog = segwit_addr.decode_segwit_address(constants.net.SEGWIT_HRP, addr)
        self.assertEqual(bytes(witprog), tweaked_pubkey)

    def test_is_taproot_address_plm(self):
        """is_taproot_address() riconosce correttamente gli indirizzi P2TR Palladium."""
        _, internal_pubkey = _make_internal_keypair()
        output_script = taproot_output_script(internal_pubkey, script_tree=None)
        addr = script_to_address(output_script)
        self.assertTrue(is_taproot_address(addr), f"Atteso taproot True per {addr!r}")

    def test_is_taproot_address_rejects_p2wpkh(self):
        """is_taproot_address() restituisce False per indirizzi P2WPKH (plm1q...)."""
        privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
        p2wpkh_addr = bitcoin.public_key_to_p2wpkh(privkey.get_public_key_bytes(compressed=True))
        self.assertFalse(is_taproot_address(p2wpkh_addr),
                         f"Atteso taproot False per P2WPKH {p2wpkh_addr!r}")

    def test_pubkey_to_address_p2tr_returns_plm1p(self):
        """bitcoin.pubkey_to_address('p2tr', ...) genera un indirizzo plm1p...."""
        privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
        # pubkey_to_address accetta hex di pubkey compresso (33 byte)
        pubkey_hex = privkey.get_public_key_bytes(compressed=True).hex()
        addr = bitcoin.pubkey_to_address('p2tr', pubkey_hex)
        self.assertTrue(addr.startswith("plm1p"), f"Expected plm1p... got: {addr!r}")

    def test_pubkey_to_address_p2tr_consistent_with_taproot_output_script(self):
        """pubkey_to_address e taproot_output_script producono lo stesso indirizzo."""
        privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
        compressed = privkey.get_public_key_bytes(compressed=True)
        # via pubkey_to_address (33-byte compressed pubkey)
        addr1 = bitcoin.pubkey_to_address('p2tr', compressed.hex())
        # via taproot_output_script (32-byte x-only pubkey)
        addr2 = script_to_address(taproot_output_script(compressed[1:], script_tree=None))
        self.assertEqual(addr1, addr2)


class TestBIP86DerivationPath(ElectrumTestCase):
    """Test riconoscimento percorso BIP-86 in xtype_from_derivation()."""

    def test_bip86_palladium_cointype(self):
        """m/86'/746'/0' è riconosciuto come p2tr (Palladium coin_type=746)."""
        self.assertEqual(xtype_from_derivation("m/86'/746'/0'"), 'p2tr')

    def test_bip86_cointype_0(self):
        """m/86'/0'/0' è riconosciuto come p2tr (Bitcoin-compat)."""
        self.assertEqual(xtype_from_derivation("m/86'/0'/0'"), 'p2tr')

    def test_bip86_cointype_1(self):
        """m/86'/1'/0' è riconosciuto come p2tr (testnet coin_type=1)."""
        self.assertEqual(xtype_from_derivation("m/86'/1'/0'"), 'p2tr')

    def test_bip84_still_p2wpkh(self):
        """m/84'/746'/0' è ancora p2wpkh (non interferisce con BIP-86)."""
        self.assertEqual(xtype_from_derivation("m/84'/746'/0'"), 'p2wpkh')

    def test_bip49_still_p2wpkh_p2sh(self):
        """m/49'/746'/0' è ancora p2wpkh-p2sh."""
        self.assertEqual(xtype_from_derivation("m/49'/746'/0'"), 'p2wpkh-p2sh')

    def test_bip44_still_standard(self):
        """m/44'/746'/0' è ancora standard."""
        self.assertEqual(xtype_from_derivation("m/44'/746'/0'"), 'standard')


class TestP2TRXpubHeaders(ElectrumTestCase):
    """Test round-trip serializzazione xpub/xprv per tipo p2tr."""

    def test_p2tr_xpub_type_roundtrip(self):
        """Un BIP32Node con xtype='p2tr' si serializza e deserializza correttamente."""
        privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
        chaincode = bytes(range(32))
        node = BIP32Node(
            xtype='p2tr',
            eckey=privkey,
            chaincode=chaincode,
        )
        xpub = node.to_xpub()
        self.assertEqual(xpub_type(xpub), 'p2tr')

    def test_p2tr_xprv_type_roundtrip(self):
        """Un BIP32Node con xtype='p2tr' serializza e deserializza correttamente xprv."""
        privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
        chaincode = bytes(range(32))
        node = BIP32Node(
            xtype='p2tr',
            eckey=privkey,
            chaincode=chaincode,
        )
        xprv = node.to_xprv()
        recovered = BIP32Node.from_xkey(xprv)
        self.assertEqual(recovered.xtype, 'p2tr')

    def test_p2tr_xpub_does_not_conflict_with_standard(self):
        """I bytes header di p2tr xpub sono diversi da quelli standard."""
        net = constants.net
        self.assertNotEqual(
            net.XPUB_HEADERS['p2tr'],
            net.XPUB_HEADERS['standard'],
        )

    def test_p2tr_xprv_does_not_conflict_with_standard(self):
        """I bytes header di p2tr xprv sono diversi da quelli standard."""
        net = constants.net
        self.assertNotEqual(
            net.XPRV_HEADERS['p2tr'],
            net.XPRV_HEADERS['standard'],
        )


class TestTRDescriptor(ElectrumTestCase):
    """Test TRDescriptor con pubkey compressi da 33 byte (wallet integration)."""

    def test_tr_descriptor_expand_from_compressed_pubkey(self):
        """TRDescriptor.expand() funziona con pubkey compressi da 33 byte."""
        privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
        compressed_hex = privkey.get_public_key_bytes(compressed=True).hex()
        # Crea il descriptor da pubkey compresso (33 byte)
        desc = get_singlesig_descriptor_from_legacy_leaf(pubkey=compressed_hex, script_type='p2tr')
        self.assertIsInstance(desc, TRDescriptor)
        # expand() non deve lanciare eccezioni
        expanded = desc.expand()
        addr = expanded.address()
        self.assertIsNotNone(addr)
        self.assertTrue(addr.startswith("plm1p"), f"Atteso plm1p... got {addr!r}")

    def test_tr_descriptor_expand_from_xonly_pubkey(self):
        """TRDescriptor.expand() funziona con pubkey x-only da 32 byte."""
        privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
        xonly_hex = privkey.get_public_key_bytes(compressed=True)[1:].hex()
        desc = get_singlesig_descriptor_from_legacy_leaf(pubkey=xonly_hex, script_type='p2tr')
        self.assertIsInstance(desc, TRDescriptor)
        expanded = desc.expand()
        addr = expanded.address()
        self.assertIsNotNone(addr)
        self.assertTrue(addr.startswith("plm1p"))

    def test_tr_descriptor_compressed_and_xonly_produce_same_address(self):
        """Un pubkey compresso e il suo x-only producono lo stesso indirizzo P2TR."""
        privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR)
        compressed_hex = privkey.get_public_key_bytes(compressed=True).hex()
        xonly_hex = privkey.get_public_key_bytes(compressed=True)[1:].hex()
        addr_compressed = get_singlesig_descriptor_from_legacy_leaf(
            pubkey=compressed_hex, script_type='p2tr').expand().address()
        addr_xonly = get_singlesig_descriptor_from_legacy_leaf(
            pubkey=xonly_hex, script_type='p2tr').expand().address()
        self.assertEqual(addr_compressed, addr_xonly)


class TestP2TRTransactionSigning(ElectrumTestCase):
    """Test firma transazioni P2TR keypath spending su rete Palladium."""

    def _build_p2tr_tx(self, privkey_bytes, internal_pubkey):
        """
        Costruisce una PartialTransaction che spende un output P2TR.
        Ritorna (tx, txin_idx).
        """
        output_script = taproot_output_script(internal_pubkey, script_tree=None)
        # Input fittizio: txid non-zero (bytes(32) sarebbe trattato come coinbase)
        dummy_txid = bytes(range(32))
        txin = PartialTxInput(prevout=TxOutpoint(txid=dummy_txid, out_idx=0))
        txin.witness_utxo = TxOutput(
            scriptpubkey=output_script,
            value=100_000,  # 100k satoshi
        )
        txin.sighash = Sighash.DEFAULT

        # Output: invia tutto a un secondo indirizzo P2TR
        privkey2 = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR + 1)
        internal_pubkey2 = privkey2.get_public_key_bytes(compressed=True)[1:]
        output_script2 = taproot_output_script(internal_pubkey2, script_tree=None)
        txout = PartialTxOutput(scriptpubkey=output_script2, value=99_000)

        tx = PartialTransaction.from_io([txin], [txout], version=2)
        return tx, 0

    def test_p2tr_keypath_sign_produces_64_byte_sig(self):
        """La firma Schnorr per keypath spending è lunga 64 byte (DEFAULT sighash)."""
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        tx, txin_idx = self._build_p2tr_tx(privkey_bytes, internal_pubkey)
        sig = tx.sign_txin(txin_idx, privkey_bytes)
        # DEFAULT sighash: signature 64 byte (no sighash suffix)
        self.assertEqual(len(sig), 64, f"Attesa sig da 64 byte, ricevuta: {len(sig)}")

    def test_p2tr_keypath_sign_completes_txin(self):
        """Dopo la firma, l'input taproot risulta completo."""
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        tx, txin_idx = self._build_p2tr_tx(privkey_bytes, internal_pubkey)
        sig = tx.sign_txin(txin_idx, privkey_bytes)
        txin = tx.inputs()[txin_idx]
        txin.witness = construct_witness([sig])
        txin.script_sig = b""
        self.assertTrue(txin.is_complete(), "Input taproot deve risultare completo dopo la firma")

    def test_p2tr_keypath_sign_sighash_all(self):
        """Firma P2TR con SIGHASH_ALL (0x01) produce 65 byte (sig + tipo)."""
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        tx, txin_idx = self._build_p2tr_tx(privkey_bytes, internal_pubkey)
        tx.inputs()[txin_idx].sighash = Sighash.ALL
        sig = tx.sign_txin(txin_idx, privkey_bytes)
        # SIGHASH_ALL: signature 64 byte + 1 byte tipo = 65 byte
        self.assertEqual(len(sig), 65, f"Attesa sig da 65 byte (ALL), ricevuta: {len(sig)}")

    def test_p2tr_keypath_deterministic(self):
        """La stessa chiave privata produce la stessa firma su preimage identico."""
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        tx1, idx1 = self._build_p2tr_tx(privkey_bytes, internal_pubkey)
        tx2, idx2 = self._build_p2tr_tx(privkey_bytes, internal_pubkey)
        sig1 = tx1.sign_txin(idx1, privkey_bytes)
        sig2 = tx2.sign_txin(idx2, privkey_bytes)
        self.assertEqual(sig1, sig2, "Firma deterministica: deve essere identica")

    def test_p2tr_sig_verifies_against_tweaked_pubkey(self):
        """La firma Schnorr si verifica correttamente contro la chiave tweaked."""
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        tx, txin_idx = self._build_p2tr_tx(privkey_bytes, internal_pubkey)
        sig = tx.sign_txin(txin_idx, privkey_bytes)
        self.assertEqual(len(sig), 64)

        # Compute tweaked pubkey (x-only, 32 bytes)
        _, tweaked_pubkey_xonly = taproot_tweak_pubkey(internal_pubkey, b"")
        # Build ECPubkey from x-only (assume even Y = 0x02 prefix)
        tweaked_ecpubkey = ecc.ECPubkey(b"\x02" + tweaked_pubkey_xonly)

        # Recompute sighash the same way sign_txin does
        pre_hash = tx.serialize_preimage(txin_idx)
        msg_hash = bip340_tagged_hash(b"TapSighash", pre_hash)

        self.assertTrue(
            tweaked_ecpubkey.schnorr_verify(sig, msg_hash),
            "Schnorr signature deve verificarsi contro la chiave tweaked"
        )

    def test_p2tr_add_sig_and_finalize_produces_correct_witness(self):
        """add_signature_to_txin + finalize_psbt produce un witness corretto (64-byte sig)."""
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        tx, txin_idx = self._build_p2tr_tx(privkey_bytes, internal_pubkey)

        # Simulate wallet signing flow: sign_txin → add_signature_to_txin → finalize_psbt
        sig = tx.sign_txin(txin_idx, privkey_bytes)
        self.assertEqual(len(sig), 64)

        # Store sig via add_signature_to_txin (mimics wallet.sign flow)
        txin = tx.inputs()[txin_idx]
        # Simulate the compressed pubkey lookup (not needed for taproot, but signature routing uses is_taproot)
        dummy_pubkey = bytes(33)
        tx.add_signature_to_txin(txin_idx=txin_idx, signing_pubkey=dummy_pubkey, sig=sig)

        self.assertEqual(txin.tap_key_sig, sig, "tap_key_sig deve essere impostato")
        self.assertIsNone(txin.witness, "witness non deve essere ancora impostato")

        # Finalize
        tx.finalize_psbt()

        witness_items = txin.witness_elements()
        self.assertEqual(len(witness_items), 1, "Witness taproot keypath deve avere 1 elemento")
        self.assertEqual(len(witness_items[0]), 64, "Il witness item deve essere 64 byte (Schnorr sig)")
        self.assertEqual(witness_items[0], sig, "Il witness item deve essere la firma Schnorr")

    def test_p2tr_full_wallet_sign_flow(self):
        """Simula il flusso completo di firma wallet (deepcopy + sign + combine)."""
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        tx, txin_idx = self._build_p2tr_tx(privkey_bytes, internal_pubkey)

        # Simula: tmp_tx = copy.deepcopy(tx); sign; combine
        tmp_tx = copy.deepcopy(tx)
        compressed_pubkey = ecc.ECPrivkey(privkey_bytes).get_public_key_bytes(compressed=True)
        keypairs = {compressed_pubkey: privkey_bytes}

        # Set script_descriptor so pubkeys property works
        desc = get_singlesig_descriptor_from_legacy_leaf(
            pubkey=compressed_pubkey.hex(), script_type='p2tr')
        tmp_tx.inputs()[txin_idx].script_descriptor = desc

        # Sign via tx.sign() (the real wallet flow)
        tmp_tx.sign(keypairs)

        # Verify tap_key_sig is set on tmp_tx input
        tmp_txin = tmp_tx.inputs()[txin_idx]
        self.assertIsNotNone(tmp_txin.tap_key_sig, "tap_key_sig deve essere impostato su tmp_tx")

        # Combine back (simula tx.combine_with_other_psbt)
        tx.inputs()[txin_idx].combine_with_other_txin(tmp_txin)

        # After combine, witness should be set on original tx
        orig_txin = tx.inputs()[txin_idx]
        self.assertIsNotNone(orig_txin.witness, "witness deve essere impostato dopo combine")
        witness_items = orig_txin.witness_elements()
        self.assertEqual(len(witness_items), 1)
        self.assertEqual(len(witness_items[0]), 64, "Schnorr sig deve essere 64 byte")

        # Verify the signature against the tweaked pubkey
        _, tweaked_pubkey_xonly = taproot_tweak_pubkey(internal_pubkey, b"")
        tweaked_ecpubkey = ecc.ECPubkey(b"\x02" + tweaked_pubkey_xonly)
        pre_hash = tx.serialize_preimage(txin_idx)
        msg_hash = bip340_tagged_hash(b"TapSighash", pre_hash)
        self.assertTrue(
            tweaked_ecpubkey.schnorr_verify(witness_items[0], msg_hash),
            "La firma nel witness deve verificarsi contro la chiave tweaked"
        )
