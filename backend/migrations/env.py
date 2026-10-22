"""
file: env.py

Alembic her komutta bu dosyayı çalıştırır. Bağlantı adresi .env'deki
MIGRATION_DATABASE_URL'den okunur. Testler başka bir veritabanında çalışmak
için adresi config.attributes["database_url"] ile verir, bu durumda .env'deki
adres kullanılmaz. MIGRATION_ROLE doluysa bağlanır bağlanmaz o role geçilir,
böylece migration'ın kurduğu her nesnenin sahibi o rol olur. Alembic'in hangi
sürümde olunduğunu tuttuğu alembic_version tablosu public'te değil alembic
şemasında durur.

description: Alembic'i projenin ayarlarıyla ve rol düzeniyle bağlayan giriş noktası.
"""

# NOTE: alembic_version ayrı bir şemada tutulur çünkü bootstrap.sql owner'ın
# public şemasında kurduğu her tabloya uygulama rolüne yazma yetkisi veriyor.
# Tablo public'te olsaydı uygulama hangi sürümde olunduğu bilgisini
# değiştirebilirdi. Uygulama rolünün alembic şemasına hiçbir yetkisi yoktur.
#
# XXX: Yeni bir modül tablo kazandığında models.py dosyası aşağıya eklenmeli.
# Import edilmeyen bir modülün tabloları Base.metadata'ya girmez ve
# autogenerate o tabloları hiç görmez, hatta var olan tabloları silmeyi
# önerebilir.

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, create_engine, pool, text

import erp.modules.currency.models  # noqa: F401  tabloları Base.metadata'ya kaydetmek için
import erp.modules.identity.models  # noqa: F401
import erp.modules.organization.models  # noqa: F401
from erp.config import Settings
from erp.infrastructure.database import Base

VERSION_SCHEMA = "alembic"

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

settings = Settings()
database_url = config.attributes.get("database_url") or settings.migration_database_url.get_secret_value()


# Rol adı dışarıdan geldiği için SQL'e doğrudan yapıştırılmaz, quote_identifier
# ile tırnaklanır. SET ROLE yer tutucu parametre kabul etmediği için başka
# bir yol yok.
def _prepare_statements(quote_identifier) -> list[str]:
    statements = []
    if settings.migration_role:
        statements.append(f"SET ROLE {quote_identifier(settings.migration_role)}")
    statements.append(f"CREATE SCHEMA IF NOT EXISTS {VERSION_SCHEMA}")
    return statements


# Offline modda veritabanına bağlanılmaz, migration'lar ekrana SQL olarak
# yazılır. Böylece bir migration'ın ne yapacağı uygulanmadan okunabilir.
# Rol geçişi ve şema kurulumu da çıktının başına yazılır, çıktı başka bir
# yerde elle çalıştırılsa bile aynı sonucu verir.
def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=Base.metadata,
        version_table_schema=VERSION_SCHEMA,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    quote = context.get_context().dialect.identifier_preparer.quote
    with context.begin_transaction():
        for statement in _prepare_statements(quote):
            context.execute(statement)
        context.run_migrations()


# SET ROLE ve CREATE SCHEMA migration'lardan önce ayrı bir transaction'da
# çalıştırılıp commit edilir. SET ROLE, SET LOCAL olmadığı için commit'ten
# sonra da bağlantı kapanana kadar geçerli kalır. Migration'lar bu yüzden
# owner kimliğiyle çalışır.
def _prepare_connection(connection: Connection) -> None:
    quote = connection.dialect.identifier_preparer.quote
    for statement in _prepare_statements(quote):
        connection.execute(text(statement))
    connection.commit()


# Her komut kendi bağlantısını açıp kapatır, NullPool bağlantıların
# komut bittikten sonra açık beklemesini engeller.
def run_migrations_online() -> None:
    engine = create_engine(database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        _prepare_connection(connection)
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            version_table_schema=VERSION_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
