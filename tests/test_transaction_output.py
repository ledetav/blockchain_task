import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from blockchain_transaction.transaction_output import TransactionOutput

class TestTransactionOutput(unittest.TestCase):

    def test_create_transaction_output_valid(self):
        tx_output = TransactionOutput("recipient_pub_key_pem", 10.5)
        self.assertEqual(tx_output.recipient_address_pubkey_pem, "recipient_pub_key_pem")
        self.assertEqual(tx_output.amount, 10.5)

    def test_create_transaction_output_amount_as_int(self):
        tx_output = TransactionOutput("recipient_pub_key_pem", 10)
        self.assertEqual(tx_output.amount, 10.0) # Должен быть float

    def test_create_transaction_output_invalid_recipient_type(self):
        with self.assertRaisesRegex(ValueError, "recipient_address_pubkey_pem должен быть непустой строкой"):
            TransactionOutput(123, 10.0) # type: ignore

    def test_create_transaction_output_empty_recipient(self):
        with self.assertRaisesRegex(ValueError, "recipient_address_pubkey_pem должен быть непустой строкой"):
            TransactionOutput("", 10.0)
            
    def test_create_transaction_output_invalid_amount_type(self):
        with self.assertRaisesRegex(ValueError, "amount должен быть положительным числом"):
            TransactionOutput("recipient_pem", "abc") # type: ignore

    def test_create_transaction_output_zero_amount(self):
        with self.assertRaisesRegex(ValueError, "amount должен быть положительным числом"):
            TransactionOutput("recipient_pem", 0)

    def test_create_transaction_output_negative_amount(self):
        with self.assertRaisesRegex(ValueError, "amount должен быть положительным числом"):
            TransactionOutput("recipient_pem", -5.0)

    def test_transaction_output_to_dict(self):
        tx_output = TransactionOutput("test_recipient_pem", 25.0)
        expected_dict = {
            'recipient_address_pubkey_pem': "test_recipient_pem",
            'amount': 25.0
        }
        self.assertEqual(tx_output.to_dict(), expected_dict)

    def test_transaction_output_repr(self):
        tx_output = TransactionOutput("a_very_long_recipient_public_key_pem_string", 50.0)
        # recipient_address_pubkey_pem='a_very_long_recipien...', amount=50.0
        self.assertTrue(repr(tx_output).startswith("TransactionOutput(recipient_address_pubkey_pem='a_very_long_recipien..."))
        self.assertTrue("amount=50.0" in repr(tx_output))

    def test_transaction_output_equality(self):
        output1 = TransactionOutput("addr1", 10.0)
        output2 = TransactionOutput("addr1", 10.0)
        output3 = TransactionOutput("addr2", 10.0)
        output4 = TransactionOutput("addr1", 20.0)

        self.assertEqual(output1, output2)
        self.assertNotEqual(output1, output3)
        self.assertNotEqual(output1, output4)
        self.assertNotEqual(output1, "not_an_output")

    def test_transaction_output_sorting(self):
        output1 = TransactionOutput("b_addr", 10.0)
        output2 = TransactionOutput("a_addr", 20.0)
        output3 = TransactionOutput("a_addr", 10.0) # Должен быть раньше output2

        outputs = [output1, output2, output3]
        sorted_outputs = sorted(outputs)

        self.assertEqual(sorted_outputs, [output3, output2, output1])


if __name__ == '__main__':
    unittest.main()