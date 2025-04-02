from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Column, String, DateTime, func
from sqlalchemy.exc import DataError, DatabaseError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Status(Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Response(Base):
    __tablename__ = "responses"

    idempotency_key = Column(String, primary_key=True)
    content = Column(JSON)
    status = Column(String, default=Status.PROCESSING.value)
    created_at = Column(DateTime, server_default=func.now())

    def __init__(self, idempotency_key: str, content: Optional[dict] = None):
        super().__init__()
        self.idempotency_key = idempotency_key
        self.content = content
        self.status = Status.PROCESSING.value


class ConflictError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ResponseRepository:
    def __init__(self, db_host: str, db_port: int, db_name: str, db_username: str, db_password: str):
        self._db_url = self._connection_string(
            "postgresql+asyncpg", db_host, db_port, db_name, db_username, db_password
        )
        self._engine = create_async_engine(self._db_url, echo=True)
        self._sessionmaker = sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_response(self, idempotency_key: str) -> Optional[Response]:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(Response).filter_by(idempotency_key=idempotency_key)
            )
            return result.scalars().first()

    async def create_response(self, response: Response) -> Response:
        async with self._sessionmaker() as session:
            try:
                session.add(response)
                await session.commit()
                await session.refresh(response)
                return response
            except IntegrityError as e:
                await session.rollback()
                raise ConflictError("The response already exists") from e
            except DataError as e:
                await session.rollback()
                raise ValueError("Response violates data integrity constraints") from e
            except DatabaseError as e:
                await session.rollback()
                raise RuntimeError("Failed to create a response") from e

    async def update_response(
        self, idempotency_key: str, **kwargs
    ) -> Optional[Response]:
        async with self._sessionmaker() as session:
            try:
                response = await session.get(Response, idempotency_key)
                if response:
                    for k, v in kwargs.items():
                        setattr(response, k, v)
                    await session.commit()
                    await session.refresh(response)
                    return response
                return None
            except (AttributeError, DataError) as e:
                await session.rollback()
                raise ValueError("Failed to update the value of an attribute") from e
            except DatabaseError as e:
                await session.rollback()
                raise RuntimeError("Failed to update a message") from e

    async def delete_response(self, idempotency_key: str) -> bool:
        async with self._sessionmaker() as session:
            try:
                response = await session.get(Response, idempotency_key)
                if response:
                    await session.delete(response)
                    await session.commit()
                    return True
                return False
            except DatabaseError as e:
                await session.rollback()
                raise RuntimeError("Failed to delete response") from e

    @staticmethod
    def _connection_string(
        db_protocol: str,
        db_host: str,
        db_port: int,
        db_name: str,
        db_username: str,
        db_password: str,
    ) -> str:
        return (
            f"{db_protocol}://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
