"""
Tests for taproot multisig (script path spending via multi_a / OP_CHECKSIGADD).
Covers:
  - multisig_tapscript_script() script format
  - MultiADescriptor expand/satisfy
  - TRDescriptor with multi_a leaf: address generation and script path satisfy
  - Tapscript sighash (ext_flag=1, tapleaf_hash)
  - Full sign → verify round-trip for 2-of-3 tapscript multisig
  - PSBT TAP_SCRIPT_SIG, TAP_LEAF_SCRIPT, TAP_INTERNAL_KEY round-trip
"""

import copy
import io

import electrum_ecc as ecc
from electrum_ecc.util import bip340_tagged_hash

from electrum import bitcoin, constants
from electrum.bitcoin import (
    taproot_output_script, taproot_tweak_pubkey, multisig_tapscript_script,
    control_block_for_taproot_script_spend, taproot_tree_helper,
    construct_witness, witness_push, opcodes,
)
from electrum.descriptor import (
    MultiADescriptor, TRDescriptor, get_singlesig_descriptor_from_legacy_leaf,
)
from electrum.descriptor import PubkeyProvider
from electrum.transaction import (
    PartialTransaction, PartialTxInput, PartialTxOutput, TxOutpoint, TxOutput,
    Transaction, Sighash, PSBTInputType,
)
from electrum.util import bfh

from . import ElectrumTestCase


def _make_keypair(scalar: int):
    """Returns (privkey_bytes, compressed_pubkey_bytes_33) for a given scalar."""
    priv = ecc.ECPrivkey.from_secret_scalar(scalar)
    return priv.get_secret_bytes(), priv.get_public_key_bytes(compressed=True)


def _make_multisig_tx(internal_scalar, leaf_scalars, thresh):
    """Build a PartialTransaction spending a P2TR output with multi_a(thresh, ...) leaf.
    Returns (tx, leaf_pairs, tr_desc) where leaf_pairs = [(priv, compressed_pk), ...]
    """
    internal_priv, internal_compressed = _make_keypair(internal_scalar)
    leaf_pairs = [_make_keypair(s) for s in leaf_scalars]

    # Build descriptor using compressed (33-byte) pubkeys — consistent with wallet flow
    internal_provider = PubkeyProvider(None, internal_compressed.hex(), None)
    leaf_providers = [PubkeyProvider(None, compressed.hex(), None) for _, compressed in leaf_pairs]
    multi_a_desc = MultiADescriptor(leaf_providers, thresh)
    tr_desc = TRDescriptor(internal_provider, multi_a_desc)

    output_script = tr_desc.expand().output_script
    dummy_txid = bytes(range(32))
    txin = PartialTxInput(prevout=TxOutpoint(txid=dummy_txid, out_idx=0))
    txin.witness_utxo = TxOutput(scriptpubkey=output_script, value=200_000)
    txin.sighash = Sighash.DEFAULT
    txin.script_descriptor = tr_desc

    recipient_xonly = _make_keypair(999)[1][1:]  # x-only for output
    txout = PartialTxOutput(
        scriptpubkey=taproot_output_script(recipient_xonly, script_tree=None),
        value=199_000,
    )
    tx = PartialTransaction.from_io([txin], [txout], version=2)
    return tx, leaf_pairs, tr_desc


class TestMultisigTapscriptScript(ElectrumTestCase):
    """Test multisig_tapscript_script() output format."""

    def test_2of2_script_opcodes(self):
        """2-of-2 tapscript: pk1 OP_CHECKSIG pk2 OP_CHECKSIGADD 2 OP_EQUAL"""
        _, pk1 = _make_keypair(1)  # compressed 33 bytes
        _, pk2 = _make_keypair(2)
        script = multisig_tapscript_script(2, [pk1, pk2])
        # parse: push(pk1_xonly) OP_CHECKSIG push(pk2_xonly) OP_CHECKSIGADD OP_2 OP_EQUAL
        self.assertIn(bytes([opcodes.OP_CHECKSIG]), script)
        self.assertIn(bytes([opcodes.OP_CHECKSIGADD]), script)
        self.assertIn(bytes([opcodes.OP_EQUAL]), script)
        # x-only pubkeys (32 bytes each) must appear in script
        self.assertIn(pk1[1:], script)
        self.assertIn(pk2[1:], script)

    def test_compressed_pubkey_stripped(self):
        """33-byte compressed pubkeys are stripped to 32-byte x-only."""
        priv = ecc.ECPrivkey.from_secret_scalar(42)
        compressed = priv.get_public_key_bytes(compressed=True)
        xonly = compressed[1:]
        script_from_compressed = multisig_tapscript_script(1, [compressed])
        script_from_xonly = multisig_tapscript_script(1, [xonly])
        self.assertEqual(script_from_compressed, script_from_xonly)

    def test_threshold_encoded(self):
        """Threshold value is encoded as OP_N in the script."""
        _, pk1 = _make_keypair(1)
        _, pk2 = _make_keypair(2)
        _, pk3 = _make_keypair(3)
        script = multisig_tapscript_script(2, [pk1, pk2, pk3])
        # OP_2 = 0x52 should appear
        self.assertIn(bytes([opcodes.OP_2]), script)


class TestMultiADescriptor(ElectrumTestCase):
    """Test MultiADescriptor expand() and satisfy()."""

    def _providers(self, *scalars):
        return [PubkeyProvider(None, _make_keypair(s)[1].hex(), None) for s in scalars]
        # Note: _make_keypair returns compressed (33-byte) pubkeys

    def test_expand_returns_tapscript(self):
        """expand() returns a valid tapscript with correct opcodes."""
        desc = MultiADescriptor(self._providers(1, 2, 3), thresh=2)
        expanded = desc.expand()
        script = expanded.output_script
        self.assertIn(bytes([opcodes.OP_CHECKSIG]), script)
        self.assertIn(bytes([opcodes.OP_CHECKSIGADD]), script)

    def test_satisfy_2of3_with_enough_sigs(self):
        """satisfy() succeeds with exactly thresh signatures (sigdata keyed by x-only)."""
        pairs = [_make_keypair(s) for s in (10, 20, 30)]
        providers = [PubkeyProvider(None, compressed.hex(), None) for _, compressed in pairs]
        desc = MultiADescriptor(providers, thresh=2)
        # Provide sigs for keys 0 and 2, keyed by x-only (32 bytes)
        fake_sig = bytes(64)
        sigdata = {pairs[0][1][1:]: fake_sig, pairs[2][1][1:]: fake_sig}
        sol = desc._satisfy_inner(sigdata=sigdata)
        # Witness reversed: items are [sig_pk3, sig_pk2, sig_pk1] in reverse order
        items = sol.witness_items
        self.assertEqual(len(items), 3)
        # pk3 (index 2) → first in witness (bottom), pk2 (index 1) → middle, pk1 (index 0) → top
        self.assertEqual(items[0], fake_sig)   # pk3 (last key, first in witness)
        self.assertEqual(items[1], b"")        # pk2 (no sig provided)
        self.assertEqual(items[2], fake_sig)   # pk1 (first key, last in witness)

    def test_satisfy_insufficient_sigs_raises(self):
        """satisfy() raises MissingSolutionPiece when not enough sigs."""
        from electrum.descriptor import MissingSolutionPiece
        pairs = [_make_keypair(s) for s in (10, 20)]
        providers = [PubkeyProvider(None, compressed.hex(), None) for _, compressed in pairs]
        desc = MultiADescriptor(providers, thresh=2)
        sigdata = {pairs[0][1][1:]: bytes(64)}  # only 1 of 2 required
        with self.assertRaises(MissingSolutionPiece):
            desc._satisfy_inner(sigdata=sigdata)

    def test_satisfy_allow_dummy(self):
        """satisfy() with allow_dummy=True fills missing sigs with dummy."""
        providers = self._providers(1, 2, 3)
        desc = MultiADescriptor(providers, thresh=2)
        sol = desc._satisfy_inner(sigdata={}, allow_dummy=True)
        items = sol.witness_items
        self.assertEqual(len(items), 3)
        # all should be dummy (64 zero bytes)
        for item in items:
            self.assertEqual(len(item), 64)

    def test_get_satisfaction_progress(self):
        """get_satisfaction_progress() counts available sigs correctly."""
        pairs = [_make_keypair(s) for s in (1, 2, 3)]
        providers = [PubkeyProvider(None, compressed.hex(), None) for _, compressed in pairs]
        desc = MultiADescriptor(providers, thresh=2)
        sigdata = {pairs[0][1][1:]: bytes(64), pairs[2][1][1:]: bytes(64)}
        have, need = desc.get_satisfaction_progress(sigdata=sigdata)
        self.assertEqual(have, 2)
        self.assertEqual(need, 2)


class TestTRDescriptorWithMultiA(ElectrumTestCase):
    """Test TRDescriptor containing multi_a script leaf."""

    def _build_tr_desc(self, thresh, leaf_scalars, internal_scalar=100):
        internal_provider = PubkeyProvider(None, _make_keypair(internal_scalar)[1].hex(), None)
        leaf_providers = [PubkeyProvider(None, _make_keypair(s)[1].hex(), None) for s in leaf_scalars]
        multi_a = MultiADescriptor(leaf_providers, thresh)
        return TRDescriptor(internal_provider, multi_a)

    def test_address_is_taproot(self):
        """tr(K, multi_a(...)) generates a valid P2TR address."""
        desc = self._build_tr_desc(2, [1, 2, 3])
        expanded = desc.expand()
        addr = expanded.address()
        self.assertIsNotNone(addr)
        self.assertTrue(bitcoin.is_taproot_address(addr))
        self.assertTrue(addr.startswith("plm1p"))

    def test_address_differs_from_keypath_only(self):
        """tr(K, multi_a(...)) address differs from tr(K) — script tree changes the tweak."""
        key = _make_keypair(100)[1]
        provider = PubkeyProvider(None, key.hex(), None)
        tr_keypath = TRDescriptor(provider)
        tr_script = self._build_tr_desc(2, [1, 2, 3], internal_scalar=100)
        self.assertNotEqual(tr_keypath.expand().output_script, tr_script.expand().output_script)

    def test_satisfy_dummy_returns_witness(self):
        """satisfy(allow_dummy=True) on tr(K, multi_a(...)) returns a non-empty witness."""
        desc = self._build_tr_desc(2, [1, 2, 3])
        sol = desc.satisfy(allow_dummy=True)
        self.assertIsNotNone(sol.witness)
        # Dummy = keypath sig (64 bytes), 1 witness item
        items_raw = sol.witness
        n_items = items_raw[0]
        self.assertGreater(n_items, 0)


class TestTaprootMultisigSigning(ElectrumTestCase):
    """Full sign → verify round-trip for tapscript multisig."""

    def _build_and_sign(self, thresh, leaf_scalars, signing_scalars):
        tx, leaf_pairs, tr_desc = _make_multisig_tx(
            internal_scalar=100, leaf_scalars=leaf_scalars, thresh=thresh
        )
        keypairs = {}
        for scalar, (priv, compressed) in zip(leaf_scalars, leaf_pairs):
            if scalar in signing_scalars:
                keypairs[compressed] = priv
        tx.sign(keypairs)
        return tx, leaf_pairs, tr_desc

    def test_2of3_signing_produces_complete_tx(self):
        """2-of-3 tapscript: sign with 2 keys → tx is complete."""
        tx, _, _ = self._build_and_sign(2, [1, 2, 3], signing_scalars=[1, 3])
        self.assertTrue(tx.is_complete(), "Transaction should be complete with 2 of 3 sigs")

    def test_1of3_signing_incomplete(self):
        """Only 1 of 3 sigs → tx is NOT complete."""
        tx, _, _ = self._build_and_sign(2, [1, 2, 3], signing_scalars=[1])
        self.assertFalse(tx.is_complete(), "Transaction should not be complete with only 1 sig")

    def test_3of3_all_sign(self):
        """All 3 sign → 3-of-3 tx is complete."""
        tx, _, _ = self._build_and_sign(3, [1, 2, 3], signing_scalars=[1, 2, 3])
        self.assertTrue(tx.is_complete())

    def test_witness_structure(self):
        """Complete tapscript tx has correct witness: [sigs..., script, control_block]."""
        tx, leaf_pairs, tr_desc = self._build_and_sign(2, [1, 2, 3], signing_scalars=[1, 2])
        self.assertTrue(tx.is_complete())
        tx.finalize_psbt()  # sets txin.witness
        txin = tx.inputs()[0]
        items = txin.witness_elements()
        # For multi_a(2, pk1, pk2, pk3): witness = [sig3_or_empty, sig2_or_empty, sig1_or_empty, script, ctrl_block]
        self.assertEqual(len(items), 5, f"Expected 5 witness items, got {len(items)}: {[i.hex() for i in items]}")
        script = items[3]
        ctrl_block = items[4]
        # Script must contain OP_CHECKSIG and OP_CHECKSIGADD
        self.assertIn(bytes([opcodes.OP_CHECKSIG]), script)
        self.assertIn(bytes([opcodes.OP_CHECKSIGADD]), script)
        # Control block: 1 byte (parity|leaf_version) + 32 bytes internal key + 0 or more 32-byte merkle nodes
        self.assertGreaterEqual(len(ctrl_block), 33)
        self.assertEqual((len(ctrl_block) - 33) % 32, 0)

    def test_tapscript_sighash_ext_flag(self):
        """Tapscript preimage uses spend_type=2 (ext_flag=1) and is longer."""
        tx, leaf_pairs, tr_desc = _make_multisig_tx(100, [1, 2, 3], 2)
        leaf_script = tr_desc.subdescriptors[0].expand().scriptcode_for_sighash
        preimage_keypath = tx.serialize_preimage(0)
        preimage_tapscript = tx.serialize_preimage(0, tapscript=(0xc0, leaf_script))
        # The two preimages must differ
        self.assertNotEqual(preimage_keypath, preimage_tapscript)
        # Tapscript adds: tapleaf_hash(32) + key_version(1) + codesep_pos(4) = 37 bytes
        self.assertEqual(len(preimage_tapscript), len(preimage_keypath) + 37)

    def test_tap_script_sigs_stored(self):
        """After signing, tap_script_sigs is populated, not tap_key_sig."""
        tx, leaf_pairs, tr_desc = _make_multisig_tx(100, [1, 2, 3], 2)
        priv1, compressed1 = leaf_pairs[0]
        keypairs = {compressed1: priv1}
        tx.sign(keypairs)
        txin = tx.inputs()[0]
        self.assertIsNone(txin.tap_key_sig, "tap_key_sig must be None for script path spend")
        self.assertGreater(len(txin.tap_script_sigs), 0, "tap_script_sigs must have entries")


class TestTapscriptPSBT(ElectrumTestCase):
    """PSBT round-trip for tapscript fields."""

    def test_tap_script_sig_psbt_roundtrip(self):
        """TAP_SCRIPT_SIG serializes and deserializes correctly."""
        tx, leaf_pairs, tr_desc = _make_multisig_tx(100, [1, 2, 3], 2)
        priv1, compressed1 = leaf_pairs[0]
        priv2, compressed2 = leaf_pairs[1]
        keypairs = {compressed1: priv1, compressed2: priv2}
        tx.sign(keypairs)
        txin = tx.inputs()[0]
        self.assertGreater(len(txin.tap_script_sigs), 0)

        # Serialize to PSBT and re-parse
        psbt_bytes = tx.serialize_as_bytes(force_psbt=True)
        tx2 = PartialTransaction.from_raw_psbt(psbt_bytes)
        txin2 = tx2.inputs()[0]
        self.assertEqual(txin.tap_script_sigs, txin2.tap_script_sigs)

    def test_tap_internal_key_psbt_roundtrip(self):
        """TAP_INTERNAL_KEY serializes and deserializes correctly."""
        tx, _, tr_desc = _make_multisig_tx(100, [1, 2], 2)
        txin = tx.inputs()[0]
        internal_compressed = tr_desc.pubkeys[0].get_pubkey_bytes()
        internal_xonly = internal_compressed[1:] if len(internal_compressed) == 33 else internal_compressed
        txin.tap_internal_key = internal_xonly

        psbt_bytes = tx.serialize_as_bytes(force_psbt=True)
        tx2 = PartialTransaction.from_raw_psbt(psbt_bytes)
        self.assertEqual(tx2.inputs()[0].tap_internal_key, internal_xonly)
