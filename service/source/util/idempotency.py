import os
from enum import Enum
from typing import Callable, Any
from typing import Optional

from .logging import global_logger as log
from ..repository import ResponseRepository, Status, Response


_repository = ResponseRepository(
    os.environ["MESSENGER_DB_HOST"],
    int(os.environ["MESSENGER_DB_PORT"]),
    os.environ["MESSENGER_DB_NAME"],
    os.environ["MESSENGER_DB_USERNAME"],
    os.environ["MESSENGER_DB_PASSWORD"],
)


class ExecutionStatus(Enum):
    SUCCEEDED = 0
    PROCESSING = 1
    REJECTED = 2


class ExecutionResult:
    def __init__(self, status: ExecutionStatus, response: Optional[Response]):
        self.status = status
        self.response = response


async def execute(
    idempotency_key: str, func: Callable[..., Any], *args, **kwargs
) -> ExecutionResult:
    existing_response = await _repository.get_response(idempotency_key)

    if existing_response:
        log.info(
            "Idempotency key found",
            key=idempotency_key,
            status=existing_response.status,
        )
        if existing_response.status == Status.COMPLETED.value:
            return ExecutionResult(ExecutionStatus.SUCCEEDED, existing_response.content)
        elif existing_response.status == Status.PROCESSING.value:
            return ExecutionResult(ExecutionStatus.PROCESSING, None)
        elif existing_response.status == Status.FAILED.value:
            return ExecutionResult(ExecutionStatus.REJECTED, None)

    try:
        await _repository.create_response(Response(idempotency_key=idempotency_key))
    except Exception as e:
        log.error(
            "Failed to acquire lock on idempotency key",
            key=idempotency_key,
            error=str(e),
        )
        raise RuntimeError("This request is already being processed.") from e

    try:
        result = await func(*args, **kwargs)
        await _repository.update_response(
            idempotency_key, content=result.model_dump(mode="json"), status=Status.COMPLETED.value
        )
        return ExecutionResult(ExecutionStatus.SUCCEEDED, result)
    except Exception as e:
        log.error(
            "Failed to update the response for idempotency key",
            key=idempotency_key,
            error=str(e),
        )
        await _repository.update_response(idempotency_key, status=Status.FAILED.value)
        raise RuntimeError(
            "Failed to update response associated with idempotency key"
        ) from e
