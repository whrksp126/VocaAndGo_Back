from app import db

from sqlalchemy import ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.schema import Column
from sqlalchemy.types import String, Integer, Date, DateTime, Boolean, Text, BigInteger

from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.types import TypeDecorator

from uuid import uuid4, UUID
from datetime import datetime, timedelta
import enum


class BinaryUUID(TypeDecorator):
    impl = BINARY(16)

    def process_bind_param(self, value, dialect=None):
        if not value:
            return None
        if isinstance(value, UUID):
            return value.bytes
        else:
            raise ValueError('value {} is not a valid UUID'.format(value))

    def process_result_value(self, value, dialect=None):
        if not value:
            return None
        else:
            return UUID(bytes=value)


class User(db.Model):
    __tablename__ = 'user'
    id = Column(BinaryUUID, primary_key=True, default=uuid4)
    email = Column(String(128), nullable=False) 
    google_id = Column(String(128), nullable=False)
    name = Column(String(32), nullable=False)
    phone = Column(String(16), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_logged_at = Column(DateTime, nullable=True, default=None)

    def __init__(self, email, google_id, name, phone):
        self.email = email
        self.google_id = google_id
        self.name = name
        self.phone = phone


# 단어
class Word(db.Model):
    __tablename__ = 'word'
    id = Column(Integer, primary_key=True)
    word = Column(String(200), nullable=True)
    pronunciation = Column(String(200), nullable=True)
    example = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


# 단어뜻
class Meaning(db.Model):
    __tablename__ = 'meaning'
    id = Column(Integer, primary_key=True)
    meaning = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    word_id = Column(Integer, ForeignKey('word.id'), nullable=True)