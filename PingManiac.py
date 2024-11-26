import json
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import JoinChannelRequest

# Чтение конфигурационного файла config.json
def load_config():
    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        print("Файл 'config.json' не найден.")
        return None
    except json.JSONDecodeError:
        print("Ошибка при чтении файла 'config.json'. Проверьте формат.")
        return None

# Функция для авторизации через номер телефона
async def start_client(api_id, api_hash):
    phone_number = input("Введите ваш номер телефона (с кодом страны): ")

    client = TelegramClient('session_name', api_id, api_hash)

    # Начинаем подключение
    await client.connect()

    if not await client.is_user_authorized():
        # Если пользователь не авторизован, отправляем код подтверждения
        await client.send_code_request(phone_number)
        code = input('Введите код подтверждения: ')
        try:
            await client.sign_in(phone_number, code)
        except SessionPasswordNeededError:
            # Запрашиваем пароль для двухфакторной аутентификации
            password = input("Введите пароль двухфакторной аутентификации: ")
            await client.sign_in(password=password)

    # Проверка авторизации
    if await client.is_user_authorized():
        print("Успешно авторизовались!")
    else:
        print("Не удалось авторизоваться.")
        return None

    return client

# Функция для загрузки списка чатов
def load_chat_links():
    chat_links = []
    try:
        with open('chats.txt', 'r') as file:
            chat_links = file.readlines()
    except FileNotFoundError:
        print("Файл 'chats.txt' не найден.")
    return [link.strip() for link in chat_links]

# Функция для отправки сообщения в чаты
async def send_message_to_chats(client, chat_links, message, delay):
    for link in chat_links:
        try:
            print(f"Обрабатываем чат: {link}")
            chat = await client.get_entity(link)  # Получаем информацию о чате

            try:
                # Проверяем, являемся ли мы участником чата
                await client.get_permissions(chat, await client.get_me())  # Проверка на участие в чате
                print(f"Вы уже являетесь участником чата {link}")
            except UserNotParticipantError:
                # Если не являемся участником, пробуем вступить
                print(f"Вы не являетесь участником чата {link}, пытаемся вступить.")
                try:
                    # Пробуем вступить в чат через прямую ссылку (t.me/имя_канала)
                    await client(JoinChannelRequest(link))
                    print(f"Успешно вступили в чат {link}")
                except Exception as e:
                    print(f"Ошибка при вступлении в чат {link}: {e}")
                    continue  # Пропускаем чат, если не удалось вступить

            # Отправка сообщения после вступления
            print(f"Отправка сообщения в чат: {link}")
            await client.send_message(chat, message)
            print(f"Сообщение отправлено в {link}")

            await asyncio.sleep(delay)  # Задержка между отправками сообщений
        except FloodWaitError as e:
            # Ожидаем, если превысили лимит сообщений
            print(f"Слишком быстро отправляем сообщения. Пауза на {e.seconds} секунд.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"Ошибка при отправке сообщения в {link}: {e}")
            continue  # Пропускаем чат, если ошибка, и продолжаем с другими чатами


# Основная программа
async def main():
    # Загрузка конфигурации из файла config.json
    config = load_config()
    if config is None:
        return

    # Извлекаем api_id и api_hash из конфигурации
    api_id = config.get('api_id')
    api_hash = config.get('api_hash')

    if not api_id or not api_hash:
        print("Не найдены api_id или api_hash в конфигурационном файле.")
        return

    # Получаем клиента Telegram
    client = await start_client(api_id, api_hash)
    if client is None:
        return

    # Загружаем список ссылок на чаты
    chat_links = load_chat_links()

    if not chat_links:
        print("Список чатов пуст!")
        return

    # Вводим сообщение для рассылки
    message = input("Введите сообщение для отправки: ")

    # Запрашиваем задержку между отправками сообщений
    while True:
        try:
            delay = float(input("Введите задержку между сообщениями (в секундах): "))
            if delay < 0:
                print("Задержка не может быть отрицательной.")
            else:
                break
        except ValueError:
            print("Введите корректное число для задержки.")

    # Отправляем сообщение с указанной задержкой
    await send_message_to_chats(client, chat_links, message, delay)

    # Завершаем сессию
    await client.disconnect()

# Запуск основного асинхронного кода
if __name__ == '__main__':
    asyncio.run(main())
