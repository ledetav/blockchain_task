import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from blockchain_transaction import (
    Transaction, TransactionInput, TransactionOutput,
    generate_rsa_keys, serialize_private_key, serialize_public_key
)

import json

def main():
    print("Генерация ключей для участников...")
    # Алиса
    alice_private_key, alice_public_key = generate_rsa_keys()
    alice_private_pem = serialize_private_key(alice_private_key)
    alice_public_pem = serialize_public_key(alice_public_key)
    print(f"Алиса Public Key (PEM начало):\n{alice_public_pem[:80]}...")

    # Боб
    bob_private_key, bob_public_key = generate_rsa_keys()
    bob_public_pem = serialize_public_key(bob_public_key)
    print(f"Боб Public Key (PEM начало):\n{bob_public_pem[:80]}...")

    # --- 1. Coinbase транзакция (первоначальное создание монет) ---
    print("\n--- Coinbase Транзакция (создание монет для Алисы) ---")
    coinbase_output = TransactionOutput(recipient_address_pubkey_pem=alice_public_pem, amount=100.0)
    coinbase_tx = Transaction(inputs=[], outputs=[coinbase_output])
    print(f"Coinbase транзакция создана: {coinbase_tx}")
    print(f"ID Coinbase транзакции: {coinbase_tx.tx_id}")
    is_coinbase_valid_placeholder = coinbase_tx.verify_signature("")
    print(f"Coinbase (без подписи пользователя) считается 'валидной' в контексте verify_signature: {is_coinbase_valid_placeholder}")

    previous_tx_for_alice_id = coinbase_tx.tx_id
    output_index_for_alice = 0

    # --- 2. Транзакция: Алиса -> Боб ---
    print("\n--- Транзакция: Алиса отправляет Бобу 25 монет ---")
    input_from_alice = TransactionInput(
        previous_tx_id=previous_tx_for_alice_id,
        output_index=output_index_for_alice
    )
    output_to_bob = TransactionOutput(recipient_address_pubkey_pem=bob_public_pem, amount=25.0)
    change_to_alice = TransactionOutput(recipient_address_pubkey_pem=alice_public_pem, amount=75.0)

    alice_to_bob_tx = Transaction(inputs=[input_from_alice], outputs=[output_to_bob, change_to_alice])
    print(f"Транзакция Алиса->Боб (до подписи): {alice_to_bob_tx}")
    print(f"Предварительный ID (хэш данных): {alice_to_bob_tx.tx_id}") # Это хэш данных

    print("Алиса подписывает транзакцию...")
    alice_to_bob_tx.sign(alice_private_pem)
    print(f"Транзакция Алиса->Боб (после подписи): {alice_to_bob_tx}")
    print(f"Финальный ID (хэш данных+подписи): {alice_to_bob_tx.tx_id}")
    if alice_to_bob_tx.signature:
        print(f"Подпись (hex начало): {alice_to_bob_tx.signature.hex()[:64]}...")

    print("Верификация подписи транзакции Алисы...")
    is_valid_alice_signature = alice_to_bob_tx.verify_signature(alice_public_pem)
    print(f"Подпись Алисы верна: {is_valid_alice_signature}")

    print("Попытка верификации подписи Алисы ключом Боба...")
    is_valid_fake = alice_to_bob_tx.verify_signature(bob_public_pem)
    print(f"Подпись Алисы верна (проверено ключом Боба): {is_valid_fake}")

    # --- Демонстрация восстановления цепочки (теоретически) ---
    print("\n--- Проверка связи транзакций ---")
    referenced_input = alice_to_bob_tx.inputs[0]
    if referenced_input.previous_tx_id == coinbase_tx.tx_id:
        print("Связь установлена: вход транзакции Алисы->Боб корректно ссылается на ID Coinbase транзакции.")
        spent_output_in_coinbase = coinbase_tx.outputs[referenced_input.output_index]
        if spent_output_in_coinbase.recipient_address_pubkey_pem == alice_public_pem:
            print(f"  И этот выход действительно предназначался Алисе (сумма {spent_output_in_coinbase.amount}).")
        else:
            print("  Ошибка: выход Coinbase не предназначался Алисе, или индекс неверен.")
    else:
        print("Ошибка: Связь транзакций нарушена!")

    # --- Демонстрация сериализации/десериализации ---
    print("\n--- Сериализация и Десериализация ---")
    tx_dict = alice_to_bob_tx.to_dict()
    print(f"Транзакция в виде словаря (начало):\n{json.dumps(tx_dict, indent=2)[:400]}...")

    reconstructed_tx = Transaction.from_dict(tx_dict)
    print(f"\nВосстановленная транзакция: {reconstructed_tx}")
    print(f"ID восстановленной транзакции: {reconstructed_tx.tx_id}")
    
    if reconstructed_tx.tx_id == alice_to_bob_tx.tx_id:
        print("ID исходной и восстановленной транзакций совпадают.")
    else:
        print("ОШИБКА: ID исходной и восстановленной транзакций НЕ совпадают.")
        print(f"  Ожидался: {alice_to_bob_tx.tx_id}")
        print(f"  Получен: {reconstructed_tx.tx_id}")


    print("Верификация подписи восстановленной транзакции...")
    is_valid_reconstructed_signature = reconstructed_tx.verify_signature(alice_public_pem)
    print(f"Подпись восстановленной транзакции верна: {is_valid_reconstructed_signature}")

if __name__ == "__main__":
    main()