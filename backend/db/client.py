from datetime import datetime

from sqlalchemy import (
    create_engine, URL, text, MetaData, ForeignKey, func, String, select, update, func, cast, \
    Integer, and_, Index, CheckConstraint, delete)
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, Mapped, mapped_column, aliased, relationship, \
    joinedload, selectinload, contains_eager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Annotated, Optional
from sqlalchemy.dialects.postgresql import insert

from backend.db.config import setting
import asyncio
import enum
from backend.db.models import Base, Users, Chats, Messages, KnowledgeBase, Participants, ChatParticipant, UserAppChats

#добавить логгер

class DatabaseClient:
    def __init__(self):
        self.async_engine = create_async_engine(url=setting.DATABASE_URL_asyncpg)
        self.async_session_factory = async_sessionmaker(self.async_engine)

    async def create_tables(self):
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("""
                       CREATE OR REPLACE FUNCTION update_updated_at_column()
                       RETURNS TRIGGER AS $$
                       BEGIN
                           NEW.updated_at = TIMEZONE('utc', now());
                           RETURN NEW;
                       END;
                       $$ language 'plpgsql';
                   """))
            tables = ["users", "chats", "knowledge_base","participants"]
            for table in tables:
                await conn.execute(text(f"DROP TRIGGER IF EXISTS set_updated_at_{table} ON {table};"))
                await conn.execute(text(f"""
                            CREATE TRIGGER set_updated_at_{table}
                            BEFORE UPDATE ON {table}
                            FOR EACH ROW
                            EXECUTE FUNCTION update_updated_at_column();
                        """))

    async def add_user(self, user_tg_id: int, username: str = None, session_string: str = None):
        update_dict = {}
        if username:
            update_dict['username'] = username
        if session_string:
            update_dict['session_string'] = session_string

        async with self.async_session_factory() as session:
            stmt = insert(Users).values(
                user_tg_id=user_tg_id,
                username=username,
                session_string=session_string,
            )
            print(stmt)
            print(update_dict)

            if update_dict:
                stmt = stmt.on_conflict_do_update(
                    index_elements=['user_tg_id'],
                    set_=update_dict
                )
            else:
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['user_tg_id']
                )
            await session.execute(stmt)
            await session.commit()

    async def add_chat(self, chat_tg_id, title=None, members=None, last_scanned_id=None):
        async with self.async_session_factory() as session:
            update_dict={}
            if title:update_dict['title']=title
            if members:update_dict['members']=members
            if last_scanned_id:update_dict['last_scanned_id']=last_scanned_id
            stmt = insert(Chats).values(
                chat_tg_id=chat_tg_id,
                title=title
            ).on_conflict_do_update(
                index_elements=['chat_tg_id'],
                set_=update_dict
            )
            await session.execute(stmt)
            await session.commit()

    async def link_user_to_chat(self, chat_id: int, user_id: int):
        async with self.async_session_factory() as session:
            stmt = insert(UserAppChats).values(
                chat_id=chat_id,
                user_id=user_id
            ).on_conflict_do_nothing()

            await session.execute(stmt)
            await session.commit()

    async def add_participant(self, user_tg_id, username):
        async with self.async_session_factory() as session:
            stmt = insert(Participants).values(
                user_tg_id=user_tg_id,
                username=username
            ).on_conflict_do_update(
                index_elements=['user_tg_id'],
                set_={
                    'username': username
                }
            )
            await session.execute(stmt)
            await session.commit()

    async def link_participant_to_chat(self, chat_id: int, participant_id: int):
        async with self.async_session_factory() as session:
            stmt = insert(ChatParticipant).values(
                chat_id=chat_id,
                participant_id=participant_id
            ).on_conflict_do_nothing()

            await session.execute(stmt)
            await session.commit()


    async def add_bulk(self, some_list: list):
        async with self.async_session_factory() as session:
            session.add_all(some_list)
            await session.commit()


    def create_message(self, msg_tg_id, id_chat, sender_id, sender_name, text, date, reply_to_id):
        return Messages(msg_tg_id=msg_tg_id,
                        chat_id=id_chat,
                        sender_id=sender_id,
                        sender_name=sender_name,
                        text=text,
                        date=date,
                        reply_to_id=reply_to_id)

    def create_qa(self, question_text, answer_text, category, chat_id):
        return KnowledgeBase(question_text=question_text,
                                       chat_id=chat_id,
                                       answer_text=answer_text,
                                       category=category)




    async def get_user_by_tg_id(self, tg_id):
        async with self.async_session_factory() as session:
            query = select(Users).where(Users.user_tg_id == tg_id)
            res = await session.execute(query)
            return res.scalar_one_or_none()


    async def get_chats(self, user_tg_id):
        async with self.async_session_factory() as session:
            query = (
                select(Chats)
                .join(UserAppChats)
                .join(Users)
                .where(Users.user_tg_id == user_tg_id)
            )
            res = await session.execute(query)
            return res.scalars().all()

    async def get_members(self, chat_tg_id):
        async with self.async_session_factory() as session:
            query = (
                select(Participants)
                .join(ChatParticipant)
                .join(Chats)
                .where(Chats.chat_tg_id == chat_tg_id)
            )
            res = await session.execute(query)
            return res.scalars().all()

    async def get_messages(
            self,
            chat_tg_id: int,
            limit: int = None,
            sender_tg_id: int = None,
            date_from: datetime = None,
            date_to: datetime = None
    ):
        async with self.async_session_factory() as session:
            query = (
                select(Messages)
                .join(Chats)
                .where(Chats.chat_tg_id == chat_tg_id)
            )
            if sender_tg_id:
                query = query.where(Messages.sender_id == sender_tg_id)
            if date_from:
                query = query.where(Messages.date >= date_from)
            if date_to:
                query = query.where(Messages.date <= date_to)

            query = query.order_by(Messages.date.desc())

            if limit:
                query = query.limit(limit)

            res = await session.execute(query)
            return res.scalars().all()

    async def get_qa(self, chat_tg_id):
        async with self.async_session_factory() as session:
            query = (
                select(Chats.knowledge_base, )
                .where(Chats.chat_tg_id == chat_tg_id)
            )
            res = await session.execute(query)
            return res.scalars().all()


    async def delete_user_chat_link(self,user_tg_id, chat_tg_id):
        async with self.async_session_factory() as session:
            user_id_sub = select(Users.id).where(Users.user_tg_id == user_tg_id).scalar_subquery()
            chat_id_sub = select(Chats.id).where(Chats.chat_tg_id == chat_tg_id).scalar_subquery()

            stmt = delete(UserAppChats).where(
                UserAppChats.user_id == user_id_sub,
                UserAppChats.chat_id == chat_id_sub
            )
            await session.execute(stmt)
            await session.commit()

    async def delete_participant(self, chat_tg_id):
        async with self.async_session_factory() as session:
            stmt = delete(Chats).where(Chats.chat_tg_id == chat_tg_id)
            await session.execute(stmt)
            await session.commit()


client=DatabaseClient()
#asyncio.run(client.create_tables())