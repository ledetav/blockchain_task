import unittest
import time
import hashlib
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from blockchain_transaction import (
    Transaction, TransactionInput, TransactionOutput,
    generate_rsa_keys, serialize_private_key, serialize_public_key
)

class CommonTestSetup(unittest.TestCase):
    """
    Базовый класс для общих настроек тестов, таких как генерация ключей.
    """
    @classmethod
    def setUpClass(cls):
        cls.alice_private_key, cls.alice_public_key = generate_rsa_keys()
        cls.alice_private_pem = serialize_private_key(cls.alice_private_key)
        cls.alice_public_pem = serialize_public_key(cls.alice_public_key)

        cls.bob_private_key, cls.bob_public_key = generate_rsa_keys()
        cls.bob_private_pem = serialize_private_key(cls.bob_private_key)
        cls.bob_public_pem = serialize_public_key(cls.bob_public_key)
        
        cls.fixed_timestamp = 1678886400.0

class TestTransactionCreation(CommonTestSetup):
    """
    Тесты, связанные с созданием транзакций и их базовыми свойствами.
    """
    def setUp(self):
        # Общая настройка для тестов создания транзакций
        self.alice_output = TransactionOutput(self.alice_public_pem, 50.0)
        self.bob_output = TransactionOutput(self.bob_public_pem, 10.0)
        self.basic_input = TransactionInput("prev_tx_id", 0)

    def test_create_coinbase_transaction(self):
        out = TransactionOutput(self.alice_public_pem, 50.0)
        tx = Transaction(inputs=[], outputs=[out], timestamp=self.fixed_timestamp)
        self.assertTrue(tx.is_coinbase())
        self.assertEqual(len(tx.inputs), 0)
        self.assertEqual(len(tx.outputs), 1)
        self.assertIsNone(tx.signature)
        self.assertIsNotNone(tx.tx_id)
        self.assertEqual(tx.timestamp, self.fixed_timestamp)

    def test_create_regular_transaction_with_inputs_and_outputs(self):
        tx = Transaction(inputs=[self.basic_input], outputs=[self.bob_output], timestamp=self.fixed_timestamp)
        self.assertFalse(tx.is_coinbase())
        self.assertEqual(len(tx.inputs), 1)
        self.assertEqual(len(tx.outputs), 1)
        self.assertEqual(tx.inputs[0], self.basic_input)
        self.assertEqual(tx.outputs[0], self.bob_output)
        self.assertIsNone(tx.signature)

    def test_transaction_requires_at_least_one_output(self):
        with self.assertRaisesRegex(ValueError, "Транзакция должна иметь хотя бы один выход"):
            Transaction(inputs=[], outputs=[])

    def test_transaction_inputs_are_sorted_by_id(self):
        inp1 = TransactionInput("tx_z", 0)
        inp2 = TransactionInput("tx_a", 1)
        out = TransactionOutput(self.alice_public_pem, 10)
        tx = Transaction(inputs=[inp1, inp2], outputs=[out])
        self.assertEqual(tx.inputs[0].previous_tx_id, "tx_a")
        self.assertEqual(tx.inputs[1].previous_tx_id, "tx_z")

    def test_transaction_outputs_are_sorted_by_recipient_address(self):
        out1 = TransactionOutput(self.bob_public_pem, 10)
        out2 = TransactionOutput(self.alice_public_pem, 20)
        tx = Transaction(inputs=[], outputs=[out1, out2])
        # Сортировка по PEM ключу, alice < bob если их ключи так соотносятся
        if self.alice_public_pem < self.bob_public_pem:
            self.assertEqual(tx.outputs[0].recipient_address_pubkey_pem, self.alice_public_pem)
            self.assertEqual(tx.outputs[1].recipient_address_pubkey_pem, self.bob_public_pem)
        else:
            self.assertEqual(tx.outputs[0].recipient_address_pubkey_pem, self.bob_public_pem)
            self.assertEqual(tx.outputs[1].recipient_address_pubkey_pem, self.alice_public_pem)

class TestTransactionSigning(CommonTestSetup):
    """
    Тесты, связанные с подписью и верификацией транзакций.
    """
    def setUp(self):
        self.inp = TransactionInput("prev_tx_for_signing", 0)
        self.out = TransactionOutput(self.bob_public_pem, 10.0)
        self.tx = Transaction(inputs=[self.inp], outputs=[self.out], timestamp=self.fixed_timestamp)

    def test_get_data_for_signing_is_deterministic(self):
        data1 = self.tx._get_data_for_signing()
        
        # Создаем "такую же" транзакцию (с тем же timestamp)
        tx2 = Transaction(inputs=[self.inp], outputs=[self.out], timestamp=self.fixed_timestamp)
        data2 = tx2._get_data_for_signing()
        self.assertEqual(data1, data2)

        # Убедимся, что json детерминирован
        expected_json_str = json.dumps({
            "timestamp": self.fixed_timestamp,
            "inputs": [self.inp.to_dict()],
            "outputs": [self.out.to_dict()]
        }, sort_keys=True, separators=(',',':'))
        self.assertEqual(data1.decode('utf-8'), expected_json_str)

    def test_calculate_initial_hash_is_consistent(self):
        initial_hash1 = self.tx._calculate_initial_hash()
        # Повторный вызов на том же объекте
        initial_hash2 = self.tx._calculate_initial_hash()
        self.assertEqual(initial_hash1, initial_hash2)
        
        # Проверка с данными для подписи
        data_for_signing = self.tx._get_data_for_signing()
        expected_hash = hashlib.sha256(data_for_signing).hexdigest()
        self.assertEqual(initial_hash1, expected_hash)

    def test_sign_sets_signature_and_updates_tx_id(self):
        initial_tx_id = self.tx.tx_id
        self.assertIsNone(self.tx.signature)
        
        self.tx.sign(self.alice_private_pem)
        
        self.assertIsNotNone(self.tx.signature)
        self.assertIsInstance(self.tx.signature, bytes)
        
        final_tx_id = self.tx.tx_id
        self.assertNotEqual(initial_tx_id, final_tx_id)
        
        expected_final_id = hashlib.sha256((initial_tx_id + self.tx.signature.hex()).encode('utf-8')).hexdigest()
        self.assertEqual(final_tx_id, expected_final_id)

    def test_sign_raises_error_if_already_signed(self):
        self.tx.sign(self.alice_private_pem)
        with self.assertRaisesRegex(ValueError, "Транзакция уже подписана."):
            self.tx.sign(self.alice_private_pem)

    def test_coinbase_sign_does_not_set_signature(self):
        out = TransactionOutput(self.alice_public_pem, 50)
        tx_coinbase = Transaction(inputs=[], outputs=[out], timestamp=self.fixed_timestamp)
        initial_id = tx_coinbase.tx_id
        tx_coinbase.sign(private_key_pem="") # Пустой ключ для coinbase
        self.assertIsNone(tx_coinbase.signature)
        self.assertEqual(tx_coinbase.tx_id, initial_id)

    def test_verify_valid_signature(self):
        self.tx.sign(self.alice_private_pem)
        self.assertTrue(self.tx.verify_signature(self.alice_public_pem))

    def test_verify_signature_with_wrong_key_returns_false(self):
        self.tx.sign(self.alice_private_pem)
        self.assertFalse(self.tx.verify_signature(self.bob_public_pem))

    def test_verify_signature_on_unsigned_transaction_returns_false(self):
        self.assertFalse(self.tx.verify_signature(self.alice_public_pem))

    def test_verify_signature_on_coinbase_unsigned_returns_true(self):
        out = TransactionOutput(self.alice_public_pem, 50)
        tx_coinbase = Transaction(inputs=[], outputs=[out])
        self.assertTrue(tx_coinbase.verify_signature(self.alice_public_pem))
        self.assertTrue(tx_coinbase.verify_signature(""))

    def test_verify_signature_tampered_data_returns_false(self):
        self.tx.sign(self.alice_private_pem)
        self.tx.outputs[0].amount = 20.0 # Изменяем данные после подписи
        self.assertFalse(self.tx.verify_signature(self.alice_public_pem))

    def test_final_tx_id_unsigned_is_initial_hash(self):
        initial_hash = self.tx._calculate_initial_hash()
        final_tx_id = self.tx._calculate_final_tx_id()
        self.assertEqual(final_tx_id, initial_hash)
        self.assertEqual(self.tx.tx_id, initial_hash)

    def test_final_tx_id_signed_is_different_from_initial_hash(self):
        initial_hash = self.tx._calculate_initial_hash()
        self.tx.sign(self.alice_private_pem)
        final_tx_id = self.tx.tx_id
        self.assertNotEqual(final_tx_id, initial_hash)
        expected_final_id = hashlib.sha256((initial_hash + self.tx.signature.hex()).encode('utf-8')).hexdigest()
        self.assertEqual(final_tx_id, expected_final_id)


class TestTransactionSerialization(CommonTestSetup):
    """
    Тесты, связанные с сериализацией и десериализацией транзакций (to_dict/from_dict).
    """
    def setUp(self):
        self.out_alice = TransactionOutput(self.alice_public_pem, 50.0)
        self.out_bob = TransactionOutput(self.bob_public_pem, 10.0)
        self.inp_basic = TransactionInput("prev_tx_for_serialization", 0)

    def test_to_dict_unsigned_transaction(self):
        tx = Transaction(inputs=[], outputs=[self.out_alice], timestamp=self.fixed_timestamp)
        tx_dict = tx.to_dict()
        
        expected_dict = {
            "tx_id": tx.tx_id,
            "timestamp": self.fixed_timestamp,
            "inputs": [],
            "outputs": [self.out_alice.to_dict()],
            "signature": None
        }
        self.assertEqual(tx_dict, expected_dict)

    def test_to_dict_signed_transaction(self):
        tx = Transaction(inputs=[self.inp_basic], outputs=[self.out_bob], timestamp=self.fixed_timestamp)
        tx.sign(self.alice_private_pem)
        tx_dict = tx.to_dict()

        expected_dict = {
            "tx_id": tx.tx_id,
            "timestamp": self.fixed_timestamp,
            "inputs": [self.inp_basic.to_dict()],
            "outputs": [self.out_bob.to_dict()],
            "signature": tx.signature.hex() if tx.signature else None
        }
        self.assertEqual(tx_dict, expected_dict)

    def test_from_dict_unsigned_transaction(self):
        tx_orig = Transaction(inputs=[], outputs=[self.out_alice], timestamp=self.fixed_timestamp)
        tx_dict = tx_orig.to_dict()

        tx_reconstructed = Transaction.from_dict(tx_dict)

        self.assertEqual(tx_reconstructed.tx_id, tx_orig.tx_id)
        self.assertEqual(tx_reconstructed.timestamp, tx_orig.timestamp)
        self.assertEqual(len(tx_reconstructed.inputs), 0)
        self.assertEqual(len(tx_reconstructed.outputs), 1)
        self.assertEqual(tx_reconstructed.outputs[0].to_dict(), self.out_alice.to_dict())
        self.assertIsNone(tx_reconstructed.signature)
        self.assertTrue(tx_reconstructed.is_coinbase())

    def test_from_dict_signed_transaction(self):
        tx_orig = Transaction(inputs=[self.inp_basic], outputs=[self.out_bob], timestamp=self.fixed_timestamp)
        tx_orig.sign(self.alice_private_pem)
        tx_dict = tx_orig.to_dict()

        tx_reconstructed = Transaction.from_dict(tx_dict)

        self.assertEqual(tx_reconstructed.tx_id, tx_orig.tx_id)
        self.assertEqual(tx_reconstructed.timestamp, tx_orig.timestamp)
        self.assertEqual(len(tx_reconstructed.inputs), 1)
        self.assertEqual(tx_reconstructed.inputs[0].to_dict(), self.inp_basic.to_dict())
        self.assertEqual(len(tx_reconstructed.outputs), 1)
        self.assertEqual(tx_reconstructed.outputs[0].to_dict(), self.out_bob.to_dict())
        self.assertIsNotNone(tx_reconstructed.signature)
        self.assertEqual(tx_reconstructed.signature, tx_orig.signature)
        self.assertFalse(tx_reconstructed.is_coinbase())
        self.assertTrue(tx_reconstructed.verify_signature(self.alice_public_pem))

    def test_from_dict_mismatched_tx_id_in_dict_is_corrected(self):
        out = TransactionOutput(self.alice_public_pem, 50.0)
        tx_orig = Transaction(inputs=[], outputs=[out], timestamp=self.fixed_timestamp)
        tx_dict = tx_orig.to_dict()
        
        original_tx_id = tx_dict['tx_id']
        tx_dict['tx_id'] = "tampered_tx_id_12345"
        
        tx_reconstructed = Transaction.from_dict(tx_dict)
        
        self.assertEqual(tx_reconstructed.tx_id, original_tx_id)
        self.assertNotEqual(tx_reconstructed.tx_id, "tampered_tx_id_12345")

if __name__ == '__main__':
    unittest.main()