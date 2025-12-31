# debug_response.py
import requests

test_data = {
    'first_name': 'Иван',
    'last_name': 'Иванов',
    'phone': '+79123456789',
    'email': 'test456@mail.ru',
    'password': 'Test123!@#',
    'confirm_password': 'Test123!@#',
    'agree_terms': 'on'
}

response = requests.post('http://localhost:8000/service/register', data=test_data)

# Сохраним ответ в файл для анализа
with open('register_response.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print("✅ Ответ сохранен в register_response.html")
print(f"📏 Размер: {len(response.text)} символов")

# Поищем ошибки в ответе
if 'уже зарегистрирован' in response.text.lower():
    print("❌ В ответе есть 'уже зарегистрирован'")

# Посмотрим первые 2000 символов
print("\n🔍 Первые 2000 символов ответа:")
print("-" * 50)
print(response.text[:2000])
print("-" * 50)