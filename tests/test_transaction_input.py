import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from blockchain_transaction.transaction_input import TransactionInput

class TestTransactionInput(unittest.TestCase):

    def test_create_transaction_input_valid(self):
        tx_input = TransactionInput("tx_id_123", 0)
        self.assertEqual(tx_input.previous_tx_id, "tx_id_123")
        self.assertEqual(tx_input.output_index, 0)

    def test_create_transaction_input_invalid_tx_id_type(self):
        with self.assertRaisesRegex(ValueError, "previous_tx_id должен быть непустой строкой"):
            TransactionInput(123, 0) # type: ignore

    def test_create_transaction_input_empty_tx_id(self):
        with self.assertRaisesRegex(ValueError, "previous_tx_id должен быть непустой строкой"):
            TransactionInput("", 0)

    def test_create_transaction_input_invalid_output_index_type(self):
        with self.assertRaisesRegex(ValueError, "output_index должен быть неотрицательным целым числом"):
            TransactionInput("tx_id_123", "abc") # type: ignore
            
    def test_create_transaction_input_negative_output_index(self):
        with self.assertRaisesRegex(ValueError, "output_index должен быть неотрицательным целым числом"):
            TransactionInput("tx_id_123", -1)

    def test_transaction_input_to_dict(self):
        tx_input = TransactionInput("tx_id_abc", 1)
        expected_dict = {
            'previous_tx_id': "tx_id_abc",
            'output_index': 1
        }
        self.assertEqual(tx_input.to_dict(), expected_dict)

    def test_transaction_input_repr(self):
        tx_input = TransactionInput("prev_tx_hash", 2)
        self.assertEqual(repr(tx_input), "TransactionInput(previous_tx_id='prev_tx_hash', output_index=2)")
        
    def test_transaction_input_equality(self):
        tx_input1 = TransactionInput("tx1", 0)
        tx_input2 = TransactionInput("tx1", 0)
        tx_input3 = TransactionInput("tx2", 0)
        tx_input4 = TransactionInput("tx1", 1)
        
        self.assertEqual(tx_input1, tx_input2)
        self.assertNotEqual(tx_input1, tx_input3)
        self.assertNotEqual(tx_input1, tx_input4)
        self.assertNotEqual(tx_input1, "not_an_input")

    def test_transaction_input_sorting(self):
        input1 = TransactionInput("a_tx_id", 1)
        input2 = TransactionInput("b_tx_id", 0)
        input3 = TransactionInput("a_tx_id", 0) # Должен быть раньше input1
        
        inputs = [input1, input2, input3]
        sorted_inputs = sorted(inputs)
        
        self.assertEqual(sorted_inputs, [input3, input1, input2])

if __name__ == '__main__':
    unittest.main()