"""
file: conftest.py

Testlerin ortak fixture'ları. Testler .env'deki adreslerle değil, bu
adreslerin veritabanı adına _test eklenmiş haliyle çalışır. Testler tabloları
kurup sildiği için adı _test ile bitmeyen bir veritabanına bağlanılacaksa test
oturumu hiçbir şey yapmadan durur.

description: Test veritabanının adresini üreten ve onu koruyan ortak fixture'lar.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import URL, Connection, Engine, create_engine, make_url, text

from erp.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_SUFFIX = "_test"


# Adres zaten _test ile bitiyorsa olduğu gibi kalır, sonuna ikinci kez
# eklenmez.
def _to_test_database(raw_url: str) -> URL:
    url = make_url(raw_url)
    if url.database and not url.database.endswith(TEST_SUFFIX):
        url = url.set(database=url.database + TEST_SUFFIX)
    return url


# _to_test_database'den sonra ayrıca kontrol edilir. Adresin nasıl üretildiği
# ileride değişse bile gerçek veritabanına dokunulmaması bu kontrole bağlıdır.
def _ensure_test_database(url: URL) -> URL:
    if not (url.database or "").endswith(TEST_SUFFIX):
        pytest.exit(
            f"Testler sadece adı {TEST_SUFFIX} ile biten bir veritabanında çalışır, verilen: {url.database}",
            returncode=2,
        )
    return url


# Ayarlar test oturumu boyunca bir kere okunur.
@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


# Migration kullanıcısının test veritabanına giden adresi. Diğer bütün
# fixture'lar adresi buradan aldığı için koruma tek bir noktada durur.
@pytest.fixture(scope="session")
def migration_url(settings: Settings) -> URL:
    url = _to_test_database(settings.migration_database_url.get_secret_value())
    return _ensure_test_database(url)


# env.py adresi config.attributes üzerinden alır. alembic.ini'ye yazmak yerine
# bu yol seçildi, çünkü ini dosyası % işaretini özel karakter sayar ve bir
# şifrede geçen % adresi bozardı.
@pytest.fixture(scope="session")
def alembic_config(migration_url: URL) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    config.attributes["database_url"] = migration_url.render_as_string(hide_password=False)
    return config


# Rol değiştirmeden bağlanır. Sadece katalogdan okuma yapan kontroller için
# yeterli, tablo kurması gereken testler owner_connection kullanır.
@pytest.fixture(scope="session")
def migration_engine(migration_url: URL) -> Iterator[Engine]:
    engine = create_engine(migration_url)
    yield engine
    engine.dispose()


# Testin yaptığı her değişiklik test bitince geri alınır, veritabanında iz
# kalmaz. MIGRATION_ROLE doluysa migration'larda olduğu gibi owner'a geçilir,
# böylece test tablo kurabilir.
@pytest.fixture
def owner_connection(migration_engine: Engine, settings: Settings) -> Iterator[Connection]:
    with migration_engine.connect() as connection:
        if settings.migration_role:
            role = connection.dialect.identifier_preparer.quote(settings.migration_role)
            connection.execute(text(f"SET LOCAL ROLE {role}"))
        yield connection
        connection.rollback()
