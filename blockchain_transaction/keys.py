from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

def generate_rsa_keys():
    """Генерирует пару RSA ключей (приватный и публичный)."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return private_key, public_key

def serialize_private_key(private_key: rsa.RSAPrivateKey) -> str:
    """Сериализует приватный ключ в формат PEM."""
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pem.decode('utf-8')

def serialize_public_key(public_key: rsa.RSAPublicKey) -> str:
    """Сериализует публичный ключ в формат PEM."""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')

def deserialize_private_key(pem_data_str: str) -> rsa.RSAPrivateKey:
    """Десериализует приватный ключ из PEM строки."""
    return serialization.load_pem_private_key(
        pem_data_str.encode('utf-8'),
        password=None
    )

def deserialize_public_key(pem_data_str: str) -> rsa.RSAPublicKey:
    """Десериализует публичный ключ из PEM строки."""
    return serialization.load_pem_public_key(
        pem_data_str.encode('utf-8')
    )