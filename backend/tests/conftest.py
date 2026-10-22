"""
file: conftest.py

Testlerin ortak fixture'ları. Testler .env'deki adreslerle değil, bu
adreslerin veritabanı adına _test eklenmiş haliyle çalışır. Testler tabloları
kurup sildiği için adı _test ile bitmeyen bir veritabanına bağlanılacaksa test
oturumu hiçbir şey yapmadan durur. Veritabanı kullanan test klasörleri
fresh_database'i kendi conftest'lerinde otomatik ister, böylece test
veritabanı oturum başında bir kere sıfırlanıp en son sürüme getirilir.
Birim testleri veritabanına hiç bağlanmaz. app_connection ve
owner_connection'ın yaptığı her değişiklik test bitince geri alınır.
Gerçekten commit eden testler clean_database ile temizlenir.

description: Test veritabanının adresini üreten, onu koruyan ve sıfırlayan ortak fixture'lar.
"""

# XXX: Sıfırlama şimdilik sadece public'teki tabloları ve fonksiyonları
# siler. Migration'lar view, enum ya da domain gibi başka türde nesneler
# kurmaya başlarsa RESET_OBJECTS'e onlar da eklenmeli, yoksa sıfırlamadan
# sonraki upgrade zaten var olan bir nesne yüzünden hata verir.

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import URL, Connection, Engine, create_engine, make_url, text

from erp.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_SUFFIX = "_test"

# public şemasının kendisi silinmez, sadece içi boşaltılır. Şema silinirse
# bootstrap.sql'in uygulama rolüne verdiği varsayılan yetkiler de onunla
# birlikte gider.
RESET_OBJECTS = """
DO $$
DECLARE
    item record;
BEGIN
    FOR item IN SELECT format('%I.%I', schemaname, tablename) AS name
                FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || item.name || ' CASCADE';
    END LOOP;
    FOR item IN SELECT p.oid::regprocedure AS name
                FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = 'public' LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS ' || item.name || ' CASCADE';
    END LOOP;
END
$$
"""


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


# SET LOCAL kullanıldığı için rol sadece açık olan transaction boyunca
# geçerlidir, transaction bitince bağlantı kendi kimliğine döner.
def _become_owner(connection: Connection, settings: Settings) -> None:
    if settings.migration_role:
        role = connection.dialect.identifier_preparer.quote(settings.migration_role)
        connection.execute(text(f"SET LOCAL ROLE {role}"))


# Ayarlar test oturumu boyunca bir kere okunur.
@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


# Migration kullanıcısının test veritabanına giden adresi. Bütün fixture'lar
# adresi buradan ya da app_url'den aldığı için koruma iki noktada durur.
@pytest.fixture(scope="session")
def migration_url(settings: Settings) -> URL:
    url = _to_test_database(settings.migration_database_url.get_secret_value())
    return _ensure_test_database(url)


# Uygulama rolünün test veritabanına giden adresi.
@pytest.fixture(scope="session")
def app_url(settings: Settings) -> URL:
    url = _to_test_database(settings.database_url.get_secret_value())
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


# Uygulama rolüyle, şifreyle ve 127.0.0.1 üzerinden bağlanır, yani uygulamanın
# kendisi nasıl bağlanacaksa öyle.
@pytest.fixture(scope="session")
def app_engine(app_url: URL) -> Iterator[Engine]:
    engine = create_engine(app_url)
    yield engine
    engine.dispose()


# anyio'nun pytest eklentisi asenkron testleri varsayılan olarak hem asyncio
# hem trio ile çalıştırmaya çalışır. Proje sadece asyncio kullanıyor.
@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


# Önceki bir oturum yarıda kesildiyse test veritabanı yarım bir sürümde
# kalmış olabilir. Her oturum bu yüzden boş bir veritabanından başlar.
@pytest.fixture(scope="session")
def fresh_database(alembic_config: Config, migration_engine: Engine, settings: Settings) -> None:
    with migration_engine.begin() as connection:
        _become_owner(connection, settings)
        connection.execute(text("DROP SCHEMA IF EXISTS alembic CASCADE"))
        connection.execute(text(RESET_OBJECTS))
    command.upgrade(alembic_config, "head")


# Testin yaptığı her değişiklik test bitince geri alınır, veritabanında iz
# kalmaz. Migration'larda olduğu gibi owner'a geçilir, böylece test tablo
# kurabilir.
@pytest.fixture
def owner_connection(migration_engine: Engine, settings: Settings) -> Iterator[Connection]:
    with migration_engine.connect() as connection:
        _become_owner(connection, settings)
        yield connection
        connection.rollback()


# Uygulamanın kendi yetkileriyle çalışan bağlantı. Değişiklikler test bitince
# geri alınır.
@pytest.fixture
def app_connection(app_engine: Engine) -> Iterator[Connection]:
    with app_engine.connect() as connection:
        yield connection
        connection.rollback()


# İstekleri gerçekten commit eden uçtan uca testler için. Test bittikten sonra
# migration'ların yüklediği para birimleri dışındaki bütün satırlar silinir.
# Sıra yabancı anahtarlara göre: önce başkasını gösteren tablolar.
@pytest.fixture
def clean_database(migration_engine: Engine, settings: Settings) -> Iterator[None]:
    yield
    with migration_engine.begin() as connection:
        _become_owner(connection, settings)
        for table in ("company", "exchange_rate", "app_user"):
            connection.execute(text(f"DELETE FROM {table}"))
