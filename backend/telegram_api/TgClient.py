from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from core.config import TELETHON_API_ID, TELETHON_API_HASH
from core.logger import logger

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
    async def send_auth_code(cls, phone: str):
        client = cls._create_client()
        await client.connect()
        try:
            result = await client.send_code_request(phone)
            temp_session = client.session.save()
            return {
                "phone_code_hash": result.phone_code_hash,
                "temp_session": temp_session,
                "status": "code_sent"
            }
        finally:
            await client.disconnect()

    @classmethod
    async def login(cls, phone: str, code: str, phone_code_hash: str, temp_session: str, password: str = None):
        client = cls._create_client(temp_session)
        await client.connect()
        try:
            if password:
                await client.sign_in(password=password)
            else:
                await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            final_session = client.session.save()
            me = await client.get_me()
            return {"status": "success", "session": final_session, "user_id": me.id, "username": me.username}

        except SessionPasswordNeededError:
            temp_after_2fa = client.session.save()
            return {
                "status": "need_password",
                "temp_session": temp_after_2fa,
            }
        except Exception as e:
            logger.error(f"Ошибка при входе: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            await client.disconnect()

    @classmethod
    async def sign_in(cls,phone, code, phone_code_hash, session_str):
        client = cls._create_client(session_str)
        await client.connect()
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        return client.session.save()

    @classmethod
    async def check_authorization(cls, session_str: str):
        if not session_str:
            return False

        client = cls._create_client(session_str)
        await client.connect()
        try:
            authorized = await client.is_user_authorized()
            return authorized
        except Exception as e:
            logger.error(f"Ошибка проверки авторизации: {e}")
            return False
        finally:
            await client.disconnect()

    @classmethod
    async def get_chats(cls, session_str: str):
        async with cls._create_client(session_str) as client:
            chats = []
            async for dialog in client.iter_dialogs():
                title = dialog.name or "Без названия"
                if dialog.is_group:
                    logger.info(f"--- Чат: {title} (ID: {dialog.id}, {"group"})")
                    chats.append({"id": dialog.id, "name": title, "kind": "group"})
            logger.info(f"Всего найдено чатов: {len(chats)}")
            return chats

    @classmethod
    async def get_messages(cls, session_str: str, target_chat: int, limit: int = 100):
        async with cls._create_client(session_str) as client:
            messages_data = []
            async for message in client.iter_messages(target_chat):
                if len(messages_data) >= limit:
                    break
                if not message.text:
                    continue
                msg_info = {
                    "date": message.date,
                    "sender_id": message.sender_id,
                    "text": message.text
                }
                messages_data.append(msg_info)
                logger.info(f"[{message.date}] ID автора: {message.sender_id} | Текст: {message.text}...")
            return messages_data
