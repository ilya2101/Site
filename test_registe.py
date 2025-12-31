# test_register.py
import requests
import json

print("🧪 Тестируем регистрацию через API")
print("=" * 50)

# Данные для регистрации
test_data = {
    'first_name': 'Иван',
    'last_name': 'Иванов',
    'phone': '+79123456789',
    'email': 'test123@mail.ru',
    'password': 'Test123!@#',
    'confirm_password': 'Test123!@#',
    'agree_terms': 'on'
}

print(f"📤 Отправляем данные:")
for key, value in test_data.items():
    if 'password' in key:
        print(f"  {key}: {'*' * len(value)}")
    else:
        print(f"  {key}: {value}")

try:
    response = requests.post(
        'http://localhost:8000/service/register',
        data=test_data,
        timeout=10
    )

    print(f"\n📥 Ответ сервера:")
    print(f"  Статус код: {response.status_code}")
    print(f"  Редирект: {response.is_redirect}")
    print(f"  HTML размер: {len(response.text)} символов")

    # Проверяем есть ли ошибки в ответе
    if 'уже зарегистрирован' in response.text:
        print(f"\n❌ ОШИБКА: В ответе есть 'уже зарегистрирован'")
        print("   Проверь HTML ответа ниже:")
        print("-" * 50)
        print(response.text[:500])  # Первые 500 символов
        print("-" * 50)
    else:
        print(f"\n✅ Ответ выглядит нормально")

except Exception as e:
    print(f"\n❌ Ошибка при отправке запроса: {e}")