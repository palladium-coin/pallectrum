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
import io
import os

import electrum_ecc as ecc
from electrum_ecc.util import bip340_tagged_hash

from electrum import bitcoin, constants, segwit_addr
from electrum.bitcoin import (
    taproot_output_script, taproot_tweak_pubkey, taproot_tweak_seckey,
    is_taproot_address, script_to_address,
    construct_witness, control_block_for_taproot_script_spend, witness_push,
)
from electrum.bip32 import BIP32Node, xpub_type
from electrum.keystore import xtype_from_derivation
from electrum.transaction import (
    Transaction, PartialTransaction, PartialTxInput, PartialTxOutput, TxOutpoint, TxOutput, Sighash,
    PSBTInputConsistencyFailure,
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


class TestP2TRScriptPathControlBlock(ElectrumTestCase):

    @staticmethod
    def _tapleaf_hash(*, leaf_version: int, script: bytes) -> bytes:
        return bip340_tagged_hash(b"TapLeaf", bytes([leaf_version]) + witness_push(script))

    @staticmethod
    def _merkle_root_from_control_block(*, leaf_hash: bytes, control_block: bytes) -> bytes:
        acc = leaf_hash
        merkle_path = control_block[33:]
        for i in range(0, len(merkle_path), 32):
            sibling = merkle_path[i:i + 32]
            if acc < sibling:
                acc = bip340_tagged_hash(b"TapBranch", acc + sibling)
            else:
                acc = bip340_tagged_hash(b"TapBranch", sibling + acc)
        return acc

    def test_control_block_reconstructs_output_key(self):
        _, internal_pubkey = _make_internal_keypair()
        leaf_script_1 = b"\x51"  # OP_TRUE
        leaf_script_2 = b"\x20" + bytes(range(32)) + b"\xac"  # PUSH32 <x> OP_CHECKSIG
        script_tree = [(0xc0, leaf_script_1), (0xc0, leaf_script_2)]

        output_spk = taproot_output_script(internal_pubkey, script_tree=script_tree)
        _, control_block = control_block_for_taproot_script_spend(
            internal_pubkey=internal_pubkey,
            script_tree=script_tree,
            script_num=0,
        )

        leaf_version = control_block[0] & 0xfe
        parity = control_block[0] & 1
        internal_key_from_cb = control_block[1:33]
        self.assertEqual(internal_key_from_cb, internal_pubkey)

        leaf_hash = self._tapleaf_hash(leaf_version=leaf_version, script=leaf_script_1)
        merkle_root = self._merkle_root_from_control_block(leaf_hash=leaf_hash, control_block=control_block)
        parity2, output_pubkey = taproot_tweak_pubkey(internal_pubkey, merkle_root)

        self.assertEqual(parity, parity2)
        self.assertEqual(output_spk, taproot_output_script(internal_pubkey, script_tree=script_tree))
        self.assertEqual(output_spk, b"\x51\x20" + output_pubkey)

    def test_corrupted_control_block_does_not_match_output_key(self):
        _, internal_pubkey = _make_internal_keypair()
        leaf_script_1 = b"\x51"
        leaf_script_2 = b"\x20" + bytes(range(32)) + b"\xac"
        script_tree = [(0xc0, leaf_script_1), (0xc0, leaf_script_2)]
        _, control_block = control_block_for_taproot_script_spend(
            internal_pubkey=internal_pubkey,
            script_tree=script_tree,
            script_num=0,
        )
        corrupted_cb = bytearray(control_block)
        corrupted_cb[33] ^= 0x01  # flip first byte of merkle path
        corrupted_cb = bytes(corrupted_cb)

        leaf_version = corrupted_cb[0] & 0xfe
        leaf_hash = self._tapleaf_hash(leaf_version=leaf_version, script=leaf_script_1)
        merkle_root_bad = self._merkle_root_from_control_block(leaf_hash=leaf_hash, control_block=corrupted_cb)
        _, output_pubkey_bad = taproot_tweak_pubkey(internal_pubkey, merkle_root_bad)
        spk_good = taproot_output_script(internal_pubkey, script_tree=script_tree)

        self.assertNotEqual(spk_good, b"\x51\x20" + output_pubkey_bad)


class TestP2TRAdvancedSigning(ElectrumTestCase):

    def _build_single_input_p2tr_tx(self, *, input_value: int = 100_000) -> tuple[PartialTransaction, int, bytes]:
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        output_script = taproot_output_script(internal_pubkey, script_tree=None)

        txin = PartialTxInput(prevout=TxOutpoint(txid=bytes(range(32)), out_idx=0))
        txin.witness_utxo = TxOutput(scriptpubkey=output_script, value=input_value)

        privkey2 = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR + 1)
        output_script2 = taproot_output_script(privkey2.get_public_key_bytes(compressed=True)[1:], script_tree=None)
        txout = PartialTxOutput(scriptpubkey=output_script2, value=input_value - 1000)

        return PartialTransaction.from_io([txin], [txout], version=2), 0, privkey_bytes

    def _build_mixed_input_tx(self, *, second_input_value: int) -> tuple[PartialTransaction, int, bytes]:
        privkey_bytes, internal_pubkey = _make_internal_keypair()
        p2tr_script = taproot_output_script(internal_pubkey, script_tree=None)

        txin0 = PartialTxInput(prevout=TxOutpoint(txid=bytes(range(32)), out_idx=0))
        txin0.witness_utxo = TxOutput(scriptpubkey=p2tr_script, value=100_000)

        legacy_spk = bfh("0014" + "22" * 20)  # p2wpkh-like witness program (non-taproot input)
        txin1 = PartialTxInput(prevout=TxOutpoint(txid=bytes(range(32, 64)), out_idx=1))
        txin1.witness_utxo = TxOutput(scriptpubkey=legacy_spk, value=second_input_value)

        output_script2 = taproot_output_script(ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR + 1)
                                               .get_public_key_bytes(compressed=True)[1:], script_tree=None)
        txout = PartialTxOutput(scriptpubkey=output_script2, value=second_input_value + 80_000)
        tx = PartialTransaction.from_io([txin0, txin1], [txout], version=2)
        return tx, 0, privkey_bytes

    def test_taproot_sighash_matrix_lengths_and_suffix(self):
        cases = [
            (Sighash.DEFAULT, 64, None),
            (Sighash.ALL, 65, Sighash.ALL),
            (Sighash.NONE, 65, Sighash.NONE),
            (Sighash.SINGLE, 65, Sighash.SINGLE),
            (Sighash.ALL | Sighash.ANYONECANPAY, 65, Sighash.ALL | Sighash.ANYONECANPAY),
            (Sighash.NONE | Sighash.ANYONECANPAY, 65, Sighash.NONE | Sighash.ANYONECANPAY),
            (Sighash.SINGLE | Sighash.ANYONECANPAY, 65, Sighash.SINGLE | Sighash.ANYONECANPAY),
        ]
        for sighash, expected_len, expected_suffix in cases:
            tx, idx, privkey = self._build_single_input_p2tr_tx()
            tx.inputs()[idx].sighash = sighash
            sig = tx.sign_txin(idx, privkey)
            self.assertEqual(len(sig), expected_len)
            if expected_suffix is not None:
                self.assertEqual(sig[-1], expected_suffix)

    def test_taproot_mixed_inputs_signature_commits_to_other_input_amounts(self):
        tx1, idx1, privkey = self._build_mixed_input_tx(second_input_value=50_000)
        tx2, idx2, _ = self._build_mixed_input_tx(second_input_value=50_001)
        sig1 = tx1.sign_txin(idx1, privkey)
        sig2 = tx2.sign_txin(idx2, privkey)
        self.assertNotEqual(sig1, sig2)

    def test_taproot_estimated_size_matches_signed_size_for_default_sighash(self):
        tx, idx, privkey = self._build_single_input_p2tr_tx()
        estimated_before_sign = tx.estimated_size()
        sig = tx.sign_txin(idx, privkey)
        tx.add_signature_to_txin(txin_idx=idx, signing_pubkey=bytes(33), sig=sig)
        tx.finalize_psbt()
        actual_size = tx.estimated_size()
        self.assertEqual(estimated_before_sign, actual_size)
        self.assertEqual(tx.get_fee(), 1000)

    def test_taproot_psbt_roundtrip_preserves_tap_fields(self):
        tx, idx, privkey = self._build_single_input_p2tr_tx()
        txin = tx.inputs()[idx]
        txin.tap_merkle_root = bytes.fromhex("11" * 32)
        txin.tap_key_sig = tx.sign_txin(idx, privkey)
        expected_sig = txin.tap_key_sig
        expected_merkle_root = txin.tap_merkle_root

        with io.BytesIO() as fd:
            tx._serialize_psbt(fd)
            raw_psbt = fd.getvalue()
        tx2 = PartialTransaction.from_raw_psbt(raw_psbt)
        tx2in = tx2.inputs()[idx]
        self.assertEqual(tx2in.tap_merkle_root, expected_merkle_root)
        self.assertEqual(tx2in.tap_key_sig, expected_sig)

        tx2.finalize_psbt()
        witness_items = tx2in.witness_elements()
        self.assertEqual(len(witness_items), 1)
        self.assertEqual(witness_items[0], expected_sig)

    def test_taproot_wrong_key_signature_does_not_verify(self):
        tx, idx, _ = self._build_single_input_p2tr_tx()
        wrong_privkey = ecc.ECPrivkey.from_secret_scalar(_TEST_SECRET_SCALAR + 999).get_secret_bytes()
        sig = tx.sign_txin(idx, wrong_privkey)

        _, internal_pubkey = _make_internal_keypair()
        _, tweaked_pubkey_xonly = taproot_tweak_pubkey(internal_pubkey, b"")
        tweaked_ecpubkey = ecc.ECPubkey(b"\x02" + tweaked_pubkey_xonly)
        msg_hash = bip340_tagged_hash(b"TapSighash", tx.serialize_preimage(idx))
        self.assertFalse(tweaked_ecpubkey.schnorr_verify(sig[:64], msg_hash))

    def test_taproot_is_complete_requires_tap_key_sig(self):
        tx, idx, privkey = self._build_single_input_p2tr_tx()
        txin = tx.inputs()[idx]
        self.assertFalse(txin.is_complete())
        txin.tap_key_sig = tx.sign_txin(idx, privkey)
        self.assertTrue(txin.is_complete())

    def test_taproot_validate_data_detects_utxo_mismatch(self):
        prev_tx = Transaction(
            "02000000000105a5a00ad10e754a17154446bbe1c557b44b86a7cd53308ad9ab813388a9d6d1520000000000fdffffff2c48659d10a752b0c0a3efa4092ebee5210943a2f41ff0607ba0e03a4cdf7bbd0000000000fdffffff93f4feb485581654caffa523c500dc417a98097fb731045040bb162acb3e14e90000000000fdffffffbf4b69292acaabf8a415db412eedd8a202d4dd2ca12e532628a756276fec00f50000000000fdffffffa96e18c45ecc56608d0be3c1b2cd93e52d569a9c3a68ed51aead570beeef29ff0000000000fdffffff017a991300000000001600142a55fbef3e419e1c862632a826ae89ade0b07e3a0247304402204de416135d26711df2cbd5209e3f79f95a1de5ddea5980215606ebfe639747bd0220286f9de38a96a078c818e97fe6fbbbe3637287461cd7407adf9e85ba6d899005012102c329033555adccaadb6c83fb486f540ba00aad3edba7a4ec3347b5cc0935c4050247304402200132c1c4c41b840f05efeacf96cccedab38d68c9021c79f940738572b049c1a302200d59ba4719d4d4e55ced651cde35cbf79838bf7122cbafd6584dd934a67db0ed01210380194ab3704b5524a0c97f78b4458b80efd365faaedaebe90fa7807eeab041700247304402202c966fbea5db4bb3794e843b59240d678a3c8e97be1d10c18475a467c101b97c02203edb0ca11e7605af2437ddffbbe416317bca8788c23c4816c13698042222d30f0121035edcdcad9affcff41302ad49a19ccbd47ae50b153ba7c2abaaf3bb2d22c859120247304402206890a622513bb9c8b8ca83e5e82532f9753ecd3188c27d8da9452e264f5500cc022012dad8fb872478b7f9d0d9d310859fca6534b8e9f44511eeef5450beaf13c690012103f683aa56e036b1307c1ae75e81553b6730aea312560e36afad487ba2bc6cf98f02473044022006807df115d6bce73e384651fbb9e932ee313133218be7769e52809b758529b6022078b2859f98a62211f130e69982f96d2968e1820c58bb817f9ab31645b6b4ceae0121026402c3c0a2b4dd5703686f8c5b5b3dcecbbf4d772ef83e440bfad22b742753e730a60300"
        )
        txout = prev_tx.outputs()[0]
        txin = PartialTxInput(prevout=TxOutpoint(txid=bytes.fromhex(prev_tx.txid()), out_idx=0))
        txin.witness_utxo = TxOutput(scriptpubkey=txout.scriptpubkey, value=txout.value + 1)
        with self.assertRaises(PSBTInputConsistencyFailure):
            txin.utxo = prev_tx
