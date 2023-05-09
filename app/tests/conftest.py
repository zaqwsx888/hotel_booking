import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import insert

from app.config import settings
from app.database import Base, async_session_maker, engine

from app.bookings.models import Bookings
from app.hotels.models import Hotels
from app.hotels.rooms.models import Rooms
from app.users.models import Users


@pytest.fixture(scope='session', autouse=True)
async def prepare_database():
    assert settings.MODE == 'TEST'

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    def open_mock_json(model: str) -> dict:
        base_dir = Path(__file__).resolve().parent
        file_path = os.path.join(base_dir, f'{model}')
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    hotels = open_mock_json('mock_hotels.json')
    rooms = open_mock_json('mock_rooms.json')
    users = open_mock_json('mock_users.json')
    bookings = open_mock_json('mock_bookings.json')

    for booking in bookings:
        # SQLAlchemy не принимает дату в текстовом формате, поэтому
        # форматируем к datetime
        booking["date_from"] = datetime.strptime(
            booking["date_from"], "%Y-%m-%d")
        booking["date_to"] = datetime.strptime(
            booking["date_to"], "%Y-%m-%d")

    async with async_session_maker() as session:
        add_hotels = insert(Hotels).values(hotels)
        add_rooms = insert(Rooms).values(rooms)
        add_users = insert(Users).values(users)
        add_bookings = insert(Bookings).values(bookings)

        await session.execute(add_hotels)
        await session.execute(add_rooms)
        await session.execute(add_users)
        await session.execute(add_bookings)

        await session.commit()


# Взято из документации к pytest-asyncio
# Создаем новый event loop для прогона тестов
@pytest.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
