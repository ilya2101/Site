# utils/phone_utils.py

import phonenumbers
from phonenumbers import NumberParseException


def normalize_phone_number(phone_raw):
    """Нормализует российский номер телефона в формат E.164"""
    if not phone_raw or not phone_raw.strip():
        return None, 'Введите номер телефона!'

    try:
        # Убираем всё кроме цифр и плюса
        cleaned = ''.join(c for c in phone_raw if c.isdigit() or c == '+')

        # Замена ведущей 8 на +7
        if cleaned.startswith('8') and len(cleaned) == 11:
            cleaned = '+7' + cleaned[1:]
        elif cleaned.startswith('7') and not cleaned.startswith('+7'):
            cleaned = '+' + cleaned

        parsed = phonenumbers.parse(cleaned, "RU")

        if not phonenumbers.is_valid_number(parsed):
            return None, 'Неверный формат номера! Пример: +79991234567'

        normalized = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return normalized, None

    except NumberParseException:
        return None, 'Неверный формат номера! Пример: +79991234567'
    except Exception as e:
        print(f"[ERROR] Phone parsing error: {e}")
        return None, 'Ошибка обработки номера телефона'