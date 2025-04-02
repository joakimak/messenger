import pytest
import asyncio
from service.source.repository import Message


def test_create_message(message_repository):
    async def test():
        message1 = await message_repository.create_message(
            Message("john.doe", "Hello, John!")
        )
        message2 = await message_repository.create_message(
            Message("jane.doe", "Hello, Jane!")
        )

        assert message1
        assert message1.id == 1
        assert message1.username == "john.doe"
        assert message1.content == "Hello, John!"
        assert message2
        assert message2.id == 2
        assert message2.username == "jane.doe"
        assert message2.content == "Hello, Jane!"

    asyncio.get_event_loop().run_until_complete(test())


def test_repository_get_message(message_repository):
    async def test():
        message1 = await message_repository.create_message(
            Message("john.doe", "Hello, John!")
        )
        message2 = await message_repository.get_message_by_id(message1.id)
        message3 = await message_repository.get_message_by_id(123)

        assert message1.id == message2.id
        assert message2.content == "Hello, John!"
        assert message3 is None

    asyncio.get_event_loop().run_until_complete(test())


def test_repository_update_message(message_repository):
    async def test():
        message1 = await message_repository.create_message(
            Message("john.doe", "Hello, John!")
        )
        message2 = await message_repository.create_message(
            Message("jane.doe", "Hello, Jane!")
        )
        message3 = await message_repository.update_message(
            message1.id, content="Hello, Charles!"
        )

        assert message1.content == "Hello, John!"
        assert message2.content == "Hello, Jane!"
        assert message3.content == "Hello, Charles!"
        with pytest.raises(ValueError):
            await message_repository.update_message(message2.id, foo="bar")

    asyncio.get_event_loop().run_until_complete(test())
