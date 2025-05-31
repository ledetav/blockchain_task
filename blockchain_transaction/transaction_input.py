class TransactionInput:
    """
    Представляет вход транзакции.
    Ссылается на выход предыдущей транзакции.
    """
    def __init__(self, previous_tx_id: str, output_index: int):
        if not isinstance(previous_tx_id, str) or not previous_tx_id:
            raise ValueError("previous_tx_id должен быть непустой строкой")
        if not isinstance(output_index, int) or output_index < 0:
            raise ValueError("output_index должен быть неотрицательным целым числом")

        self.previous_tx_id = previous_tx_id
        self.output_index = output_index

    def to_dict(self) -> dict:
        """Возвращает словарь для сериализации."""
        return {
            'previous_tx_id': self.previous_tx_id,
            'output_index': self.output_index
        }

    def __repr__(self) -> str:
        return (f"TransactionInput(previous_tx_id='{self.previous_tx_id}', "
                f"output_index={self.output_index})")

    def __eq__(self, other) -> bool:
        if not isinstance(other, TransactionInput):
            return NotImplemented
        return (self.previous_tx_id == other.previous_tx_id and
                self.output_index == other.output_index)

    def __lt__(self, other) -> bool: # Для сортировки
        if not isinstance(other, TransactionInput):
            return NotImplemented
        if self.previous_tx_id != other.previous_tx_id:
            return self.previous_tx_id < other.previous_tx_id
        return self.output_index < other.output_index