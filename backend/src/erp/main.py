"""
file: main.py
importable: create_app

Uygulamanın kurulduğu yer. create_app ayarları alır, veritabanı bağlantısını,
hata işleyicilerini ve modüllerin uç noktalarını birleştirip FastAPI
uygulamasını döndürür. Modül seviyesinde hazır bir uygulama nesnesi yoktur,
sunucu uygulamayı fabrika olarak çağırır:

    uv run uvicorn erp.main:create_app --factory

Testler create_app'e kendi ayarlarını vererek uygulamayı test veritabanına
bağlar.

description: FastAPI uygulamasını parçalarından kuran giriş noktası.
"""

# NOTE: Modül seviyesinde app = create_app() yazılmadı. Öyle olsaydı bu
# dosyayı import eden her şey, testler dahil, .env'i okuyup gerçek
# veritabanına bağlanacak bir uygulama kurardı.

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from erp.config import Settings
from erp.infrastructure.database import create_database_engine, create_session_factory
from erp.modules.currency.api import router as currency_router
from erp.modules.organization.api import router as company_router
from erp.web.errors import register_error_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    """Uygulamayı kurar.

    Args:
        settings: Uygulamanın ayarları. Verilmezse ortamdan ve .env'den okunur.

    Returns:
        Uç noktaları ve hata işleyicileri bağlanmış uygulama.
    """
    settings = settings or Settings()

    # Engine uygulama açılırken kurulur, kapanırken havuzdaki bağlantılar
    # kapatılır. Oturum üreticisi app.state'e konur, her istek kendi oturumunu
    # buradan alır.
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(settings.database_url.get_secret_value())
        app.state.session_factory = create_session_factory(engine)
        yield
        await engine.dispose()

    app = FastAPI(
        title="pakt-erp",
        description="Sıfırdan tasarlanan bir ERP sisteminin sunucu tarafı.",
        version="0.1.0",
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.include_router(currency_router)
    app.include_router(company_router)
    return app
