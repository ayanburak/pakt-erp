"""
file: test_migrations.py

Migration'ların test veritabanında ileri ve geri alınabildiğini ve ilk
migration'ın kurduğu set_updated_at() fonksiyonunun doğru çalıştığını
doğrular. Testler sonunda test veritabanını en son sürümde bırakır.

description: Migration'ların ileri ve geri alınabilirliğini ve ilk migration'ı test eder.
"""

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, Engine, text


# to_regprocedure, verilen imzada bir fonksiyon yoksa hata vermek yerine NULL
# döndürür, böylece varlık kontrolü tek sorguyla yapılır.
def _function_exists(engine: Engine, signature: str) -> bool:
    with engine.connect() as connection:
        return connection.execute(text("SELECT to_regprocedure(:s) IS NOT NULL"), {"s": signature}).scalar_one()


# Altyapı adımının bitiş ölçütü: ilk sürüm uygulanır, geri alınır ve tekrar
# uygulanır, her adımda fonksiyonun varlığı kontrol edilir.
def test_upgrade_and_downgrade(alembic_config: Config, migration_engine: Engine) -> None:
    command.upgrade(alembic_config, "head")
    assert _function_exists(migration_engine, "set_updated_at()")

    command.downgrade(alembic_config, "base")
    assert not _function_exists(migration_engine, "set_updated_at()")

    command.upgrade(alembic_config, "head")
    assert _function_exists(migration_engine, "set_updated_at()")


# Tablo testin transaction'ı içinde kurulur ve owner_connection test bitince
# geri aldığı için veritabanında kalmaz. now() transaction'ın başladığı anı
# verdiği için güncellenen satırın zamanı aynı transaction'daki now() ile
# birebir eşit olmalı.
def test_set_updated_at_fills_updated_at(alembic_config: Config, owner_connection: Connection) -> None:
    command.upgrade(alembic_config, "head")
    owner_connection.execute(text("CREATE TABLE item (id int, name text, updated_at timestamptz)"))
    owner_connection.execute(text(
        "CREATE TRIGGER item_updated_at BEFORE UPDATE ON item "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))
    owner_connection.execute(text("INSERT INTO item VALUES (1, 'ilk', NULL)"))
    owner_connection.execute(text("UPDATE item SET name = 'ikinci'"))

    assert owner_connection.execute(text("SELECT updated_at = now() FROM item")).scalar_one()


# Merdiven testi: her migration tek tek ileri, bir adım geri ve tekrar ileri
# alınır. Bir migration'ın downgrade'i upgrade'in yaptığı her şeyi geri
# almıyorsa ikinci upgrade zaten var olan bir nesneyi kurmaya çalışırken
# hata verir. Yeni migration'lar eklendikçe bu test onları da kendiliğinden kapsar.
def test_migrations_stairway(alembic_config: Config) -> None:
    script = ScriptDirectory.from_config(alembic_config)
    revisions = list(script.walk_revisions("base", "heads"))
    revisions.reverse()

    command.downgrade(alembic_config, "base")
    for revision in revisions:
        command.upgrade(alembic_config, revision.revision)
        command.downgrade(alembic_config, "-1")
        command.upgrade(alembic_config, revision.revision)
