import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status, Query, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .util.logging import global_logger as log
from .util.idempotency import ExecutionStatus, execute
from .repository import MessageRepository, Message


message_repository = MessageRepository(
    os.environ["MESSENGER_DB_HOST"],
    int(os.environ["MESSENGER_DB_PORT"]),
    os.environ["MESSENGER_DB_NAME"],
    os.environ["MESSENGER_DB_USERNAME"],
    os.environ["MESSENGER_DB_PASSWORD"],
)


class MessageResponse(BaseModel):
    message_id: int
    username: str
    content: str
    is_read: bool
    created_at: datetime


class PaginatedMessageResponse(BaseModel):
    messages: list[MessageResponse]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int


class MessageRequest(BaseModel):
    username: str
    content: str


class MessagesDeleteResponse(BaseModel):
    deleted: list[int]
    not_deleted: list[int]


app = FastAPI()


@app.middleware("/")
async def decorate_request(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    log.add_mdc("correlation_id", correlation_id)
    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(req: Request, e: Exception):
    log.error(
        "Received a value exception",
        method=req.method,
        request=str(req.url),
        error=str(e),
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(ValueError)
async def global_exception_handler(req: Request, e: Exception):
    log.warn(
        "Received a value exception",
        method=req.method,
        request=str(req.url),
        error=str(e),
    )
    return JSONResponse(status_code=400, content={"detail": "Bad request"})


@app.get("/health", status_code=status.HTTP_200_OK)
async def check_health():
    log.info("Checking health")


@app.get(
    "/message/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_message(message_id: int):
    log.info("Received request to get message", message_id=message_id)
    message = await message_repository.get_message_by_id(message_id)
    if message:
        return MessageResponse(
            message_id=message.id,
            username=message.username,
            content=message.content,
            is_read=message.is_read,
            created_at=message.created_at,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found",
        )


@app.get(
    "/message/", response_model=PaginatedMessageResponse, status_code=status.HTTP_200_OK
)
async def get_messages(
    include_read: bool = True,
    username: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    query = {}
    if username:
        query["username"] = username
    if not include_read:
        query["is_read"] = False

    total_items = await message_repository.count_messages(**query)
    total_pages = (total_items + size - 1) // size
    start = (page - 1) * size
    end = start + size

    messages = await message_repository.get_messages(start, end, **query)
    return PaginatedMessageResponse(
        messages=[
            MessageResponse(
                message_id=m.id,
                username=m.username,
                content=m.content,
                created_at=m.created_at,
                is_read=m.is_read,
            )
            for m in messages
        ],
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=size,
    )


@app.post(
    "/message/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def post_message(
    message_request: MessageRequest,
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
):
    log.info("Received request to create a message", username=message_request.username)

    async def create_message(message: Message) -> MessageResponse:
        msg = await message_repository.create_message(message)
        return MessageResponse(
            message_id=msg.id,
            username=msg.username,
            content=msg.content,
            is_read=msg.is_read,
            created_at=msg.created_at,
        )

    message = Message(message_request.username, message_request.content)
    if idempotency_key:
        log.info("Processing message idempotently", key=idempotency_key)

        result = await execute(idempotency_key, create_message, message)
        if result.status is ExecutionStatus.SUCCEEDED:
            return MessageResponse.model_validate(result.response)
        elif result.status is ExecutionStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Request is already being processed",
            )
        elif result.status is ExecutionStatus.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Previous execution failed"
            )

    return await create_message(message)


@app.put(
    "/message/{message_id}/read",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def put_message_read(message_id: int):
    log.info("Received request to mark a message as read", message_id=message_id)
    message = await message_repository.update_message(message_id, is_read=True)
    if message:
        return MessageResponse(
            message_id=message.id,
            username=message.username,
            content=message.content,
            is_read=message.is_read,
            created_at=message.created_at,
        )
    else:
        raise HTTPException(
            status_code=404, detail=f"Message {message_id} doesn't exist"
        )


@app.delete("/message/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: int):
    log.info("Received request to delete a message", message_id=message_id)
    success = await message_repository.delete_message(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="The message does not exist")


@app.delete(
    "/message/",
    response_model=MessagesDeleteResponse,
    status_code=status.HTTP_207_MULTI_STATUS,
)
async def delete_messages(message_ids: list[int] = Query(...)):
    log.info("Received request to delete multiple messages", message_ids=message_ids)
    payload = {"deleted": [], "not_deleted": []}
    for i in message_ids:
        try:
            success = await message_repository.delete_message(i)
            payload["deleted" if success else "not_deleted"].append(i)
        except RuntimeError as _:
            payload["not_deleted"] = i
            log.error("Failed to delete message", message_id=i)
    return MessagesDeleteResponse(**payload)
