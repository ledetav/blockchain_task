class TransactionOutput:
    """
    Представляет выход транзакции.
    Определяет, кому и сколько средств передается.
    """
    def __init__(self, recipient_address_pubkey_pem: str, amount: float):
        if not isinstance(recipient_address_pubkey_pem, str) or not recipient_address_pubkey_pem:
            raise ValueError("recipient_address_pubkey_pem должен быть непустой строкой")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("amount должен быть положительным числом")

        self.recipient_address_pubkey_pem = recipient_address_pubkey_pem
        self.amount = float(amount)

    def to_dict(self) -> dict:
        """Возвращает словарь для сериализации."""
        return {
            'recipient_address_pubkey_pem': self.recipient_address_pubkey_pem,
            'amount': self.amount
        }

    def __repr__(self) -> str:
        return (f"TransactionOutput(recipient_address_pubkey_pem="
                f"'{self.recipient_address_pubkey_pem[:20]}...', amount={self.amount})")

    def __eq__(self, other) -> bool:
        if not isinstance(other, TransactionOutput):
            return NotImplemented
        return (self.recipient_address_pubkey_pem == other.recipient_address_pubkey_pem and
                self.amount == other.amount)

    def __lt__(self, other) -> bool: # Для сортировки
        if not isinstance(other, TransactionOutput):
            return NotImplemented
        if self.recipient_address_pubkey_pem != other.recipient_address_pubkey_pem:
            return self.recipient_address_pubkey_pem < other.recipient_address_pubkey_pem
        return self.amount < other.amount