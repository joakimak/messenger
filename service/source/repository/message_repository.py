import datetime
from typing import Optional, List
from urllib.parse import quote_plus

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.exc import DataError, DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_read = Column(Boolean, default=False)

    def __init__(self, username: str, content: str):
        super().__init__()
        self.username = username
        self.content = content
        self.is_read = False
        self.created_at = datetime.datetime.now()

    def __repr__(self):
        return (
            f"Message(id={self.id}, username={self.username}, message={self.content}, "
            f"is_read={self.is_read}, created_at={self.created_at})"
        )

    @classmethod
    def columns(cls):
        return [column.name for column in cls.__table__.columns]


class MessageRepository:
    def __init__(self, db_host: str, db_port: int, db_name: str, db_username: str, db_password: str):
        self._db_url = self._connection_string(
            "postgresql+asyncpg", db_host, db_port, db_name, db_username, db_password
        )
        self._engine = create_async_engine(self._db_url, echo=True)
        self._sessionmaker = sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def count_messages(self, **kwargs) -> int:
        async with self._sessionmaker() as session:
            query = select(func.count(Message.id))
            if kwargs:
                query = query.filter_by(**kwargs)
            result = await session.execute(query)
            return result.scalar_one()

    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        async with self._sessionmaker() as session:
            result = await session.execute(select(Message).filter_by(id=message_id))
            return result.scalars().first()

    async def get_messages(self, i: int, j: int, **kwargs) -> List[Message]:
        async with self._sessionmaker() as session:
            query = (
                select(Message)
                .order_by(Message.created_at.desc())
                .offset(i)
                .limit(j - i)
            )
            if kwargs:
                query = query.filter_by(**kwargs)
            result = await session.execute(query)
            return result.scalars().all()

    async def create_message(self, message: Message) -> Message:
        async with self._sessionmaker() as session:
            try:
                session.add(message)
                await session.commit()
                await session.refresh(message)
                return message
            except DataError as e:
                await session.rollback()
                raise ValueError("Message violates data integrity constraints") from e
            except DatabaseError as e:
                await session.rollback()
                raise RuntimeError("Failed to create a message") from e

    async def update_message(self, message_id: int, **kwargs) -> Optional[Message]:
        async with self._sessionmaker() as session:
            try:
                message = await session.get(Message, message_id)
                if message:
                    for k, v in kwargs.items():
                        if k not in Message.columns():
                            raise AttributeError(f"Attribute {k} does not exist on Message")
                        setattr(message, k, v)
                    await session.commit()
                    await session.refresh(message)
                    return message
                return None
            except (AttributeError, DataError) as e:
                await session.rollback()
                raise ValueError("Failed to update the value of an attribute") from e
            except DatabaseError as e:
                await session.rollback()
                raise RuntimeError("Failed to update a message") from e

    async def delete_message(self, message_id: int) -> bool:
        async with self._sessionmaker() as session:
            try:
                message = await session.get(Message, message_id)
                if message:
                    await session.delete(message)
                    await session.commit()
                    return True
                return False
            except DatabaseError as e:
                await session.rollback()
                raise RuntimeError("Failed to delete message") from e

    @staticmethod
    def _connection_string(
        db_protocol, db_host, db_port, db_name, db_username, db_password
    ) -> str:
        return f"{db_protocol}://{db_username}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"
