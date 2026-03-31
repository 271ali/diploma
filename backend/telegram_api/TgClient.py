from telethon import TelegramClient
from telethon.sessions import StringSession
from core.config import TELETHON_API_ID, TELETHON_API_HASH
from core.logger import logger
import os

class TgClient:
    @staticmethod
    def _create_client(session_str: str = None):
        session = StringSession(session_str) if session_str else StringSession()
        """Проверка для файлоф сесси (локально):
        if session_name_or_str and not session_name_or_str.startswith("1"):
                    session_path = os.path.join(SESSION_DIR, session_name_or_str)
                    return TelegramClient(session_path, TELETHON_API_ID, TELETHON_API_HASH)
             """
        return TelegramClient(session, TELETHON_API_ID, TELETHON_API_HASH)


    @classmethod
    async def login_and_save(cls):
        async with cls._create_client() as client:
            me = await client.get_me()
            session_str = client.session.save()
            logger.info(f"Client {me.id} successfully saved session: {session_str}")
            return session_str, me.id

    @classmethod
    async def get_chats(cls, session_str: str):
        async with cls._create_client(session_str) as client:
            count = 0
            chats = []
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    logger.info(f"--- Нашел чат: {dialog.name} (ID: {dialog.id})")
                    chats.append({"id": dialog.id, "name": dialog.name})
                    count += 1
            logger.info(f"Всего найдено чатов: {count}")
            return chats

    @classmethod
    async def get_messages(cls, session_str: str, target_chat: int, limit: int = 100):
        async with cls._create_client(session_str) as client:
            messages_data = []
            async for message in client.iter_messages(target_chat, limit=limit):
                msg_info = {
                    "date": message.date,
                    "sender_id": message.sender_id,
                    "text": message.text
                }
                messages_data.append(msg_info)
                logger.info(f"[{message.date}] ID автора: {message.sender_id} | Текст: {message.text[:30]}...")
            return messages_data


"""Для FastAPI
async def send_auth_code(phone):
    client = TgClient._create_client()
    await client.connect()
    phone_code_hash = (await client.send_code_request(phone)).phone_code_hash
    return phone_code_hash, client.session.save() 

async def sign_in(phone, code, phone_code_hash, session_str):
    client = TgClient._create_client(session_str)
    await client.connect()
    await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
    return client.session.save()"""