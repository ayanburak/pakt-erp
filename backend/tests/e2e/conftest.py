"""
file: conftest.py

Uçtan uca testlerin ortak fixture'ları. client, test veritabanına bağlı
gerçek bir uygulamaya gerçek HTTP istekleri gönderir, ama ağ üzerinden değil
doğrudan bellekte. İstekler gerçekten commit ettiği için her testten sonra
veritabanı temizlenir.

description: Uygulamayı test veritabanıyla kurup ona HTTP istemcisi veren fixture'lar.
"""

from collections.abc import AsyncIterator

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import URL

from erp.config import Settings
from erp.main import create_app


@pytest.fixture(autouse=True)
def _database(fresh_database: None, clean_database: None) -> None:
    pass


# httpx'in ASGITransport'u uygulamanın lifespan'ini çalıştırmaz, bu yüzden
# engine'i kuran lifespan burada elle açılıp kapatılır. model_copy yeni
# değeri doğrulamadan koyduğu için adres SecretStr'e burada elle sarılır.
@pytest.fixture
async def client(app_url: URL, settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    database_url = SecretStr(app_url.render_as_string(hide_password=False))
    test_settings = settings.model_copy(update={"database_url": database_url})
    app = create_app(test_settings)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
