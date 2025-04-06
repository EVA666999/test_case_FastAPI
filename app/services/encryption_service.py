import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


class EncryptionService:
    """Простой сервис шифрования"""

    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

    _cipher = Fernet(
        ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
    )

    @classmethod
    def encrypt(cls, data: str) -> str:
        """Шифрует текст"""
        if not data:
            return data

        return cls._cipher.encrypt(data.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_data: str) -> str:
        """Расшифровывает текст"""
        if not encrypted_data:
            return encrypted_data

        try:
            return cls._cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            print(f"Ошибка расшифровки: {e}")
            return None
