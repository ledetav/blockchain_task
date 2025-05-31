import hashlib
import json
import time
from typing import List, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from .transaction_input import TransactionInput
from .transaction_output import TransactionOutput
from .keys import deserialize_private_key, deserialize_public_key, serialize_public_key # Для recipient_address

class Transaction:
    """
    Представляет транзакцию в блокчейне.
    Содержит входы, выходы и подпись.
    """
    def __init__(self, inputs: List[TransactionInput], outputs: List[TransactionOutput], timestamp: Optional[float] = None):
        if not all(isinstance(i, TransactionInput) for i in inputs):
            raise ValueError("Все элементы inputs должны быть экземплярами TransactionInput")
        if not all(isinstance(o, TransactionOutput) for o in outputs):
            raise ValueError("Все элементы outputs должны быть экземплярами TransactionOutput")
        if not outputs:
            raise ValueError("Транзакция должна иметь хотя бы один выход")

        self.inputs = sorted(inputs) # Сортировка для детерминизма
        self.outputs = sorted(outputs) # Сортировка для детерминизма
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.signature: Optional[bytes] = None
        self.tx_id: str = self._calculate_initial_hash()

    def _get_data_for_signing(self) -> bytes:
        """
        Собирает данные транзакции (без подписи) в каноническом виде для хеширования и подписи.
        """
        tx_data = {
            "timestamp": self.timestamp,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs]
        }
        return json.dumps(tx_data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def _calculate_initial_hash(self) -> str:
        """
        Вычисляет SHA256 хэш данных транзакции (до подписи).
        Этот хэш будет подписан.
        """
        return hashlib.sha256(self._get_data_for_signing()).hexdigest()

    def sign(self, private_key_pem: str):
        """
        Подписывает транзакцию с использованием приватного ключа (в PEM).
        Подписывается хэш данных транзакции.
        После подписи обновляется финальный tx_id.
        """
        if not self.inputs and self.signature is not None:
            pass
        elif self.signature is not None:
            raise ValueError("Транзакция уже подписана.")
        if not self.inputs and not private_key_pem:
            pass
        elif not private_key_pem:
            raise ValueError("Приватный ключ необходим для подписи.")


        private_key = deserialize_private_key(private_key_pem)
        data_hash_to_sign = self._calculate_initial_hash().encode('utf-8')

        self.signature = private_key.sign(
            data_hash_to_sign,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        self.tx_id = self._calculate_final_tx_id()

    def _calculate_final_tx_id(self) -> str:
        """
        Вычисляет финальный ID транзакции.
        Если не подписана: хэш данных.
        Если подписана: хэш (хэша данных + подписи).
        """
        initial_hash = self._calculate_initial_hash()
        if not self.signature:
            return initial_hash

        combined_data = initial_hash + self.signature.hex()
        return hashlib.sha256(combined_data.encode('utf-8')).hexdigest()

    def verify_signature(self, sender_public_key_pem: str) -> bool:
        """
        Проверяет подпись транзакции с использованием публичного ключа отправителя (в PEM).
        Для coinbase транзакций (без входов) эта проверка обычно не нужна или обрабатывается иначе.
        """
        if self.is_coinbase():
            return self.signature is None

        if not self.signature:
            return False
        if not sender_public_key_pem:
            return False

        public_key = deserialize_public_key(sender_public_key_pem)
        original_data_hash = self._calculate_initial_hash().encode('utf-8')

        try:
            public_key.verify(
                self.signature,
                original_data_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False

    def is_coinbase(self) -> bool:
        """Проверяет, является ли транзакция coinbase (без входов)."""
        return not self.inputs

    def __repr__(self) -> str:
        signature_status = "Signed" if self.signature else "Unsigned"
        cb_status = " (Coinbase)" if self.is_coinbase() else ""
        return (f"Transaction(id={self.tx_id[:10]}..., "
                f"inputs_count={len(self.inputs)}, "
                f"outputs_count={len(self.outputs)}, "
                f"status={signature_status}{cb_status})")

    def to_dict(self) -> dict:
        """Представляет транзакцию в виде словаря для легкой сериализации/хранения."""
        return {
            "tx_id": self.tx_id,
            "timestamp": self.timestamp,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs],
            "signature": self.signature.hex() if self.signature else None
        }

    @classmethod
    def from_dict(cls, tx_data: dict):
        """Восстанавливает транзакцию из словаря."""
        inputs = [TransactionInput(**inp_data) for inp_data in tx_data.get('inputs', [])]
        outputs = [TransactionOutput(**out_data) for out_data in tx_data.get('outputs', [])]
        
        if not outputs:
             raise ValueError("Данные для транзакции должны содержать 'outputs'")

        tx = cls(inputs, outputs, timestamp=tx_data.get('timestamp'))
        
        signature_hex = tx_data.get('signature')
        if signature_hex:
            tx.signature = bytes.fromhex(signature_hex)
        
        calculated_final_tx_id = tx._calculate_final_tx_id()
        if tx_data.get('tx_id') and tx_data['tx_id'] != calculated_final_tx_id:
            pass
        tx.tx_id = calculated_final_tx_id

        return tx