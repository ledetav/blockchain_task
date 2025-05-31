import unittest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from blockchain_transaction.keys import (
    generate_rsa_keys,
    serialize_private_key,
    serialize_public_key,
    deserialize_private_key,
    deserialize_public_key
)

class TestKeys(unittest.TestCase):

    def test_generate_rsa_keys_returns_tuple(self):
        keys = generate_rsa_keys()
        self.assertIsInstance(keys, tuple)
        self.assertEqual(len(keys), 2)

    def test_generate_rsa_keys_private_key_type(self):
        private_key, _ = generate_rsa_keys()
        self.assertIsInstance(private_key, rsa.RSAPrivateKey)

    def test_generate_rsa_keys_public_key_type(self):
        _, public_key = generate_rsa_keys()
        self.assertIsInstance(public_key, rsa.RSAPublicKey)

    def test_serialize_deserialize_private_key(self):
        private_key, _ = generate_rsa_keys()
        pem_private = serialize_private_key(private_key)
        self.assertIsInstance(pem_private, str)
        self.assertTrue(pem_private.startswith("-----BEGIN PRIVATE KEY-----"))
        
        deserialized_private_key = deserialize_private_key(pem_private)
        self.assertEqual(private_key.private_numbers(), deserialized_private_key.private_numbers())

    def test_deserialize_private_key_invalid_pem_raises_error(self):
        with self.assertRaises(ValueError): # Или специфичное исключение cryptography
            deserialize_private_key("invalid pem data")

    def test_serialize_deserialize_public_key(self):
        _, public_key = generate_rsa_keys()
        pem_public = serialize_public_key(public_key)
        self.assertIsInstance(pem_public, str)
        self.assertTrue(pem_public.startswith("-----BEGIN PUBLIC KEY-----"))

        deserialized_public_key = deserialize_public_key(pem_public)
        self.assertEqual(public_key.public_numbers(), deserialized_public_key.public_numbers())
        
    def test_deserialize_public_key_invalid_pem_raises_error(self):
        with self.assertRaises(ValueError): # Или специфичное исключение cryptography
            deserialize_public_key("invalid pem data")

    def test_key_consistency_sign_verify(self):
        private_key, public_key = generate_rsa_keys()
        
        pem_private = serialize_private_key(private_key)
        pem_public = serialize_public_key(public_key)
        
        deserialized_private = deserialize_private_key(pem_private)
        deserialized_public = deserialize_public_key(pem_public)
        
        message = b"test message for signing"
        signature = deserialized_private.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        try:
            deserialized_public.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            verified = True
        except Exception:
            verified = False
        self.assertTrue(verified, "Signature verification failed with deserialized keys")

if __name__ == '__main__':
    unittest.main()