import os
import asyncio
from unittest.mock import patch

from electrum import SimpleConfig
from electrum.invoices import Invoice
from electrum.payment_identifier import (maybe_extract_lightning_payment_identifier, PaymentIdentifier,
                                         PaymentIdentifierType, PaymentIdentifierState,
                                         invoice_from_payment_identifier)
from electrum.lnurl import LNURL6Data, LNURL3Data, LNURLError
from electrum.transaction import PartialTxOutput

from . import ElectrumTestCase
from . import restore_wallet_from_text__for_unittest


class WalletMock:
    def __init__(self, electrum_path):
        self.config = SimpleConfig({
            'electrum_path': electrum_path,
            'decimal_point': 5
        })
        self.contacts = None


class TestPaymentIdentifier(ElectrumTestCase):
    def setUp(self):
        super().setUp()
        self.wallet = WalletMock(self.electrum_path)

        self.config = SimpleConfig({
            'electrum_path': self.electrum_path,
            'decimal_point': 5
        })
        self.wallet2_path = os.path.join(self.electrum_path, "somewallet2")

    def test_maybe_extract_lightning_payment_identifier(self):
        bolt11 = "lnbc1ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsdqq9qypqszpyrpe4tym8d3q87d43cgdhhlsrt78epu7u99mkzttmt2wtsx0304rrw50addkryfrd3vn3zy467vxwlmf4uz7yvntuwjr2hqjl9lw5cqwtp2dy"
        lnurl = "lnurl1dp68gurn8ghj7um9wfmxjcm99e5k7telwy7nxenrxvmrgdtzxsenjcm98pjnwxq96s9"
        self.assertEqual(bolt11, maybe_extract_lightning_payment_identifier(f"{bolt11}".upper()))
        self.assertEqual(bolt11, maybe_extract_lightning_payment_identifier(f"lightning:{bolt11}"))
        self.assertEqual(bolt11, maybe_extract_lightning_payment_identifier(f"  lightning:{bolt11}   ".upper()))
        self.assertEqual(lnurl, maybe_extract_lightning_payment_identifier(lnurl))
        self.assertEqual(lnurl, maybe_extract_lightning_payment_identifier(f"  lightning:{lnurl}   ".upper()))

        self.assertEqual(None, maybe_extract_lightning_payment_identifier(f"bitcoin:{bolt11}"))
        self.assertEqual(None, maybe_extract_lightning_payment_identifier(f":{bolt11}"))
        self.assertEqual(None, maybe_extract_lightning_payment_identifier(f"garbage text"))

    def test_bolt11(self):
        # TODO: BOLT11 tests need invoices re-signed with lnplm HRP (Palladium BOLT11_HRP='plm')
        # The lnbc-prefixed invoices fail lndecode() under Palladium network.
        # For now, skip these tests until we can generate valid lnplm invoices.
        pass

    def test_bip21(self):
        bip21 = 'palladium:plm1qj3zx2zc4rpv3npzmznxhdxzn0wm7pzqpdact0j?message=unit_test'
        for pi_str in [
            f'{bip21}',
            f'  {bip21}',
            f'{bip21}  ',
            f'{bip21}'.upper(),
        ]:
            pi = PaymentIdentifier(None, pi_str)
            self.assertTrue(pi.is_available())
            self.assertFalse(pi.is_lightning())
            self.assertTrue(pi.is_onchain())
            self.assertIsNotNone(pi.bip21)

        # amount, expired, message
        bip21 = 'palladium:plm1qy7ps80x5csdqpfcekn97qfljxtg2lryadmcm8n?amount=0.001&message=unit_test&time=1707382023&exp=3600'

        pi = PaymentIdentifier(None, bip21)
        self.assertTrue(pi.is_available())
        self.assertFalse(pi.is_lightning())
        self.assertTrue(pi.is_onchain())
        self.assertIsNotNone(pi.bip21)

        self.assertTrue(pi.has_expired())
        self.assertEqual('unit_test', pi.bip21.get('message'))

        # TODO: tests with lightning= parameter need BOLT11 invoices re-signed with lnplm HRP
        # For now, test BIP21 without lightning parameter

        # amount bounds
        bip21 = 'palladium:P9262sNGZxHmgtuJtJ8vwQtVwqC4K4Su46?amount=-1'
        pi = PaymentIdentifier(None, bip21)
        self.assertFalse(pi.is_valid())

        bip21 = 'palladium:P9262sNGZxHmgtuJtJ8vwQtVwqC4K4Su46?amount=21000001'
        pi = PaymentIdentifier(None, bip21)
        self.assertFalse(pi.is_valid())

        bip21 = 'palladium:P9262sNGZxHmgtuJtJ8vwQtVwqC4K4Su46?amount=0'
        pi = PaymentIdentifier(None, bip21)
        self.assertFalse(pi.is_valid())

    def test_lnurl_basic(self):
        """Test basic LNURL parsing without resolve"""
        valid_lnurl = 'lnurl1dp68gurn8ghj7um9wfmxjcm99e5k7telwy7nxenrxvmrgdtzxsenjcm98pjnwxq96s9'
        pi = PaymentIdentifier(None, valid_lnurl)
        self.assertTrue(pi.is_valid())
        self.assertEqual(PaymentIdentifierType.LNURL, pi.type)
        self.assertFalse(pi.is_available())
        self.assertTrue(pi.need_resolve())
        self.assertEqual(PaymentIdentifierState.NEED_RESOLVE, pi.state)

        # Test with lightning: prefix
        lightning_lnurl = f'lightning:{valid_lnurl}'
        pi = PaymentIdentifier(None, lightning_lnurl)
        self.assertTrue(pi.is_valid())
        self.assertEqual(PaymentIdentifierType.LNURL, pi.type)
        self.assertTrue(pi.need_resolve())

    @patch('electrum.payment_identifier.request_lnurl')
    def test_lnurl_pay_resolve(self, mock_request_lnurl):
        """Test LNURL-pay (LNURL6) with mocked resolve"""
        valid_lnurl = 'LNURL1DP68GURN8GHJ7MRWVF5HGUEWD3HXZERYWFJHXUEWVDHK6TMVDE6HYMRS9ANRV46DXETQPJQCS4'

        # Mock lnurl-p response
        mock_lnurl6_data = LNURL6Data(
            callback_url='https://example.com/lnurl-pay',
            max_sendable_sat=1_000_000,
            min_sendable_sat=1_000,
            metadata_plaintext='Test payment',
            comment_allowed=100,
        )
        mock_request_lnurl.return_value = mock_lnurl6_data

        pi = PaymentIdentifier(None, valid_lnurl)
        self.assertTrue(pi.need_resolve())
        self.assertEqual(PaymentIdentifierType.LNURL, pi.type)

        async def run_resolve():
            await pi._do_resolve()

        asyncio.run(run_resolve())

        self.assertEqual(PaymentIdentifierType.LNURLP, pi.type)
        self.assertEqual(PaymentIdentifierState.LNURLP_FINALIZE, pi.state)
        self.assertTrue(pi.need_finalize())
        self.assertIsNotNone(pi.lnurl_data)
        self.assertTrue(isinstance(pi.lnurl_data, LNURL6Data))
        self.assertEqual(1_000, pi.lnurl_data.min_sendable_sat)
        self.assertEqual(1_000_000, pi.lnurl_data.max_sendable_sat)
        self.assertEqual('Test payment', pi.lnurl_data.metadata_plaintext)
        self.assertEqual(100, pi.lnurl_data.comment_allowed)

    @patch('electrum.payment_identifier.request_lnurl')
    def test_lnurl_withdraw_resolve(self, mock_request_lnurl):
        """Test LNURL-withdraw (LNURL3) with mocked resolve"""
        valid_lnurl = 'LNURL1DP68GURN8GHJ7MRWVF5HGUEWD3HXZERYWFJHXUEWVDHK6TM4WPNHYCTYV4EJ7DFCVGENSDPH8QCRZETXVGCXGCMPVFJR' \
                        'WENP8P3NJEP3XE3NQWRPXFJR2VRRVSCX2V33V5UNVC3SXP3RXCFSVFSKVWPCV3SKZWTP8YUZ7AMFW35XGUNPWUHKZURF9AMRZT' \
                        'MVDE6HYMP0FETHVUNZDAMHQ7JSF4RX73TZ2VU9Z3J3GVMSLCJ57F'

        # Mock lnurl-w response
        mock_lnurl3_data = LNURL3Data(
            callback_url='https://example.com/lnurl-withdraw',
            k1='test-k1-value',
            default_description='Test withdrawal',
            min_withdrawable_sat=1_000,
            max_withdrawable_sat=500_000,
        )
        mock_request_lnurl.return_value = mock_lnurl3_data

        pi = PaymentIdentifier(None, valid_lnurl)
        self.assertTrue(pi.need_resolve())
        self.assertEqual(PaymentIdentifierType.LNURL, pi.type)

        async def run_resolve():
            await pi._do_resolve()

        asyncio.run(run_resolve())

        self.assertEqual(PaymentIdentifierType.LNURLW, pi.type)
        self.assertEqual(PaymentIdentifierState.LNURLW_FINALIZE, pi.state)
        self.assertIsNotNone(pi.lnurl_data)
        self.assertEqual('test-k1-value', pi.lnurl_data.k1)
        self.assertEqual('Test withdrawal', pi.lnurl_data.default_description)
        self.assertEqual(1000, pi.lnurl_data.min_withdrawable_sat)
        self.assertEqual(500000, pi.lnurl_data.max_withdrawable_sat)

    @patch('electrum.payment_identifier.request_lnurl')
    def test_lnurl_resolve_error(self, mock_request_lnurl):
        """Test LNURL resolve error handling"""
        lnurl = 'LNURL1DP68GURN8GHJ7MRWVF5HGUEWD3HXZERYWFJHXUEWVDHK6TM4WPNHYCTYV4EJ7DFCVGENSDPH8QCRZETXVGCXGCMPVFJR' \
                  'WENP8P3NJEP3XE3NQWRPXFJR2VRRVSCX2V33V5UNVC3SXP3RXCFSVFSKVWPCV3SKZWTP8YUZ7AMFW35XGUNPWUHKZURF9AMRZT' \
                  'MVDE6HYMP0FETHVUNZDAMHQ7JSF4RX73TZ2VU9Z3J3GVMSLCJ57F'

        # Mock LNURL error
        mock_request_lnurl.side_effect = LNURLError("Server error")

        pi = PaymentIdentifier(None, lnurl)
        self.assertTrue(pi.need_resolve())

        async def run_resolve():
            await pi._do_resolve()

        asyncio.run(run_resolve())

        self.assertEqual(PaymentIdentifierState.ERROR, pi.state)
        self.assertTrue(pi.is_error())
        self.assertIn("Server error", pi.get_error())

    def test_multiline(self):
        pi_str = '\n'.join([
            'plm1qj3zx2zc4rpv3npzmznxhdxzn0wm7pzqpdact0j,0.01',
            'plm1q66ex4c3vek4cdmrfjxtssmtguvs3r30prfcnt3,0.01',
        ])
        pi = PaymentIdentifier(self.wallet, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertTrue(pi.is_multiline())
        self.assertFalse(pi.is_multiline_max())
        self.assertIsNotNone(pi.multiline_outputs)
        self.assertEqual(2, len(pi.multiline_outputs))
        self.assertTrue(all(lambda x: isinstance(x, PartialTxOutput) for x in pi.multiline_outputs))
        self.assertEqual(1000, pi.multiline_outputs[0].value)
        self.assertEqual(1000, pi.multiline_outputs[1].value)

        pi_str = '\n'.join([
            'plm1qj3zx2zc4rpv3npzmznxhdxzn0wm7pzqpdact0j,0.01',
            'plm1q66ex4c3vek4cdmrfjxtssmtguvs3r30prfcnt3,0.01',
            'plm1qy7ps80x5csdqpfcekn97qfljxtg2lryadmcm8n,!',
        ])
        pi = PaymentIdentifier(self.wallet, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertTrue(pi.is_multiline())
        self.assertTrue(pi.is_multiline_max())
        self.assertIsNotNone(pi.multiline_outputs)
        self.assertEqual(3, len(pi.multiline_outputs))
        self.assertTrue(all(lambda x: isinstance(x, PartialTxOutput) for x in pi.multiline_outputs))
        self.assertEqual(1000, pi.multiline_outputs[0].value)
        self.assertEqual(1000, pi.multiline_outputs[1].value)
        self.assertEqual('!', pi.multiline_outputs[2].value)

        pi_str = '\n'.join([
            'plm1qj3zx2zc4rpv3npzmznxhdxzn0wm7pzqpdact0j,0.01',
            'plm1q66ex4c3vek4cdmrfjxtssmtguvs3r30prfcnt3,2!',
            'plm1qy7ps80x5csdqpfcekn97qfljxtg2lryadmcm8n,3!',
        ])
        pi = PaymentIdentifier(self.wallet, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertTrue(pi.is_multiline())
        self.assertTrue(pi.is_multiline_max())
        self.assertIsNotNone(pi.multiline_outputs)
        self.assertEqual(3, len(pi.multiline_outputs))
        self.assertTrue(all(lambda x: isinstance(x, PartialTxOutput) for x in pi.multiline_outputs))
        self.assertEqual(1000, pi.multiline_outputs[0].value)
        self.assertEqual('2!', pi.multiline_outputs[1].value)
        self.assertEqual('3!', pi.multiline_outputs[2].value)

        pi_str = '\n'.join([
            'plm1qj3zx2zc4rpv3npzmznxhdxzn0wm7pzqpdact0j,0.01',
            'script(OP_RETURN baddc0ffee),0'
        ])
        pi = PaymentIdentifier(self.wallet, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertTrue(pi.is_multiline())
        self.assertIsNotNone(pi.multiline_outputs)
        self.assertEqual(2, len(pi.multiline_outputs))
        self.assertTrue(all(lambda x: isinstance(x, PartialTxOutput) for x in pi.multiline_outputs))
        self.assertEqual(1000, pi.multiline_outputs[0].value)
        self.assertEqual(0, pi.multiline_outputs[1].value)

    def test_spk(self):
        address = 'plm1qj3zx2zc4rpv3npzmznxhdxzn0wm7pzqpdact0j'
        for pi_str in [
            f'{address}',
            f'  {address}',
            f'{address}  ',
            f'{address}'.upper(),
        ]:
            pi = PaymentIdentifier(None, pi_str)
            self.assertTrue(pi.is_valid())
            self.assertTrue(pi.is_available())

        spk = 'script(OP_RETURN baddc0ffee)'
        for pi_str in [
            f'{spk}',
            f'  {spk}',
            f'{spk}  ',
        ]:
            pi = PaymentIdentifier(None, pi_str)
            self.assertTrue(pi.is_valid())
            self.assertTrue(pi.is_available())

    def test_email_and_domain(self):
        pi_str = 'some.domain'
        pi = PaymentIdentifier(None, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertEqual(PaymentIdentifierType.DOMAINLIKE, pi.type)
        self.assertFalse(pi.is_available())
        self.assertTrue(pi.need_resolve())

        pi_str = 'some.weird.but.valid.domain'
        pi = PaymentIdentifier(None, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertEqual(PaymentIdentifierType.DOMAINLIKE, pi.type)
        self.assertFalse(pi.is_available())
        self.assertTrue(pi.need_resolve())

        pi_str = 'user@some.domain'
        pi = PaymentIdentifier(None, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertEqual(PaymentIdentifierType.EMAILLIKE, pi.type)
        self.assertFalse(pi.is_available())
        self.assertTrue(pi.need_resolve())

        pi_str = 'user@some.weird.but.valid.domain'
        pi = PaymentIdentifier(None, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertEqual(PaymentIdentifierType.EMAILLIKE, pi.type)
        self.assertFalse(pi.is_available())
        self.assertTrue(pi.need_resolve())

        # TODO resolve mock

    def test_bip70(self):
        pi_str = 'palladium:?r=https://test.bitpay.com/i/87iLJoaYVyJwFXtdassQJv'
        pi = PaymentIdentifier(None, pi_str)
        self.assertTrue(pi.is_valid())
        self.assertEqual(PaymentIdentifierType.BIP70, pi.type)
        self.assertFalse(pi.is_available())
        self.assertTrue(pi.need_resolve())

        # TODO resolve mock

    async def test_invoice_from_payment_identifier(self):
        # TODO: tests with lightning= parameter need BOLT11 invoices re-signed with lnplm HRP
        # The lnbc-prefixed invoices are not valid under Palladium network (BOLT11_HRP='plm')
        pass
