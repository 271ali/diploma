import asyncio
from backend.telegram_api.TgClient import TgClient
async def run_test():
    print("--- ТЕСТ МОДУЛЯ АВТОРИЗАЦИИ ---")

    phone = input("Введите номер телефона (в формате +375...): ")
    result = await TgClient.send_auth_code(phone)

    if result["status"] != "code_sent":
        print(f"Ошибка при отправке кода: {result}")
        return

    print("Код успешно отправлен в Telegram!")

    phone_code_hash = result["phone_code_hash"]
    temp_session = result["temp_session"]

    # 2. Ввод кода и проверка
    code = input("Введите 5-значный код из Telegram: ")
    login_result = await TgClient.login(
        phone=phone,
        code=code,
        phone_code_hash=phone_code_hash,
        temp_session=temp_session
    )

    # 3. Обработка двухфакторки (пароля), если нужно
    if login_result["status"] == "need_password":
        print("У вас установлена двухфакторная аутентификация.")
        password = input("Введите ваш облачный пароль: ")
        temp_session = login_result["temp_session"]
        login_result = await TgClient.login(
            phone=phone,
            code=code,
            phone_code_hash=phone_code_hash,
            temp_session=temp_session,
            password=password
        )

    # 4. Проверка финального результата
    if login_result["status"] == "success":
        final_session = login_result["session"]
        user_id = login_result["user_id"]
        print(f"\nУспешный вход! ID пользователя: {user_id}")
        print(f"Ваша финальная строка сессии (сохраните её в БД):\n{final_session}\n")

        # 5. Тестируем получение чатов
        print("--- Получение списка групп ---")
        chats = await TgClient.get_chats(final_session)

        if chats:
            print(f"Найдено групп: {len(chats)}")
            # Берем первую группу для теста сообщений
            target_chat_id = chats[0]['id']
            target_chat_name = chats[0]['name']

            print(f"\n--- Получение сообщений из группы: {target_chat_name} ---")
            messages = await TgClient.get_messages(final_session, target_chat_id, limit=5)
            print(f"Загружено {len(messages)} сообщений.")
        else:
            print("Группы не найдены.")

    else:
        print(f"Ошибка входа: {login_result.get('message', 'Неизвестная ошибка')}")


if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        pass