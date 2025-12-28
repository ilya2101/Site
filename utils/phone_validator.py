import phonenumbers
from phonenumbers import NumberParseException, region_code_for_country_code

def normalize_phone(raw: str, allowed_regions=("RU", "BY")) -> str | None:
    """
    Возвращает +71234567890 или None, если номер не RU/BY либо невалиден.
    """
    if not raw:
        return None

    # phonenumbers парсит только строки, начинающиеся с «+» или «00»
    # если пользователь ввёл 8 905… → заменим 8 на +7
    stripped = raw.strip()
    if stripped.startswith("8") and len(stripped) == 11:
        stripped = "+7" + stripped[1:]

    try:
        num = phonenumbers.parse(stripped, None)  # без дефолтного региона
    except NumberParseException:
        return None

    if not phonenumbers.is_valid_number(num):
        return None

    region = region_code_for_country_code(num.country_code)
    if region not in allowed_regions:          # разрешены только RU/BY
        return None

    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)