from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class Message(BaseModel):
    msg_tg_id: int
    sender_id: int
    sender_username: Optional[str] = None
    text: str
    date: datetime
    toxicity_score: float = 0.0
    model_config = ConfigDict(from_attributes=True)


class Participant(BaseModel):
    user_tg_id: int
    username: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class KnowledgeBase(BaseModel):
    question_text: str
    answer_text: str
    category: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class Chat(BaseModel):
    chat_tg_id: int
    title: str
    last_scanned_id: int
    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    user_tg_id: int
    username: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)