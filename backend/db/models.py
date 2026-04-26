from datetime import datetime

from sqlalchemy import text, ForeignKey,String, BigInteger, Text
from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column, relationship
from typing import Annotated, Optional

int_pk=Annotated[int,mapped_column(primary_key=True)]
tg_id = Annotated[int, mapped_column(BigInteger, unique=True)]

date_time=Annotated[datetime,mapped_column(server_default=text("TIMEZONE('utc',now())"))]


class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__='users'
    id: Mapped[int_pk]
    user_tg_id: Mapped[tg_id]
    username:Mapped[str]
    session_string: Mapped[Optional[str]]
    created_at: Mapped[date_time]
    updated_at: Mapped[date_time]
    chats: Mapped[list["Chats"]] = relationship(
        back_populates="app_users",
        secondary="user_app_chats"
    )

class UserAppChats(Base):
    __tablename__ = 'user_app_chats'
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        primary_key=True)


class Chats(Base):
    __tablename__='chats'
    id: Mapped[int_pk]
    chat_tg_id: Mapped[tg_id]
    title:Mapped[str] = mapped_column(String(200))
    last_scanned_id: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at:Mapped[date_time]
    updated_at:Mapped[date_time]
    messages: Mapped[list["Messages"]] = relationship(
        back_populates="chat",
        primaryjoin="Chats.id==Messages.chat_id",
        cascade="all, delete-orphan"
    )
    knowledge_base: Mapped[list["KnowledgeBase"]] = relationship(
        back_populates="chat",
        primaryjoin="Chats.id==KnowledgeBase.chat_id",
        cascade="all, delete-orphan"
    )
    participants: Mapped[list["Participants"]] = relationship(
        secondary="chat_participants",
        back_populates="chats",
    )
    app_users: Mapped[list["Users"]] = relationship(
        secondary="user_app_chats",
        back_populates="chats"
    )


class Participants(Base):
    __tablename__ = 'participants'
    id: Mapped[int_pk]
    user_tg_id: Mapped[tg_id]
    username: Mapped[str]
    chats: Mapped[list["Chats"]] = relationship(
        secondary="chat_participants",
        back_populates="participants"
    )
    created_at: Mapped[date_time]
    updated_at: Mapped[date_time]

class ChatParticipant(Base):
    __tablename__ = 'chat_participants'

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"),primary_key=True)


class Messages(Base):
    __tablename__ = "messages"

    id: Mapped[int_pk]
    msg_tg_id: Mapped[str]

    chat_id:Mapped[int]=mapped_column(ForeignKey('chats.id',ondelete='cascade'))
    chat: Mapped["Chats"] = relationship(back_populates="messages")

    sender_id: Mapped[int] = mapped_column(BigInteger)
    sender_name: Mapped[Optional[str]]

    text: Mapped[str]
    date: Mapped[datetime]

    reply_to_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    toxicity_score: Mapped[float] = mapped_column(default=0.0)
    topic: Mapped[Optional[str]]


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id: Mapped[int_pk]
    question_text: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str] = mapped_column(Text)

    category: Mapped[Optional[str]]
    created_at: Mapped[date_time]
    updated_at: Mapped[date_time]

    chat_id: Mapped[int]=mapped_column(ForeignKey('chats.id',ondelete='cascade'))
    chat: Mapped["Chats"] = relationship(back_populates="knowledge_base")








