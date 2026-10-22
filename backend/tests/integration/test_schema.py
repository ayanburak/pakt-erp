"""
file: test_schema.py

currency, exchange_rate, company ve app_user tablolarındaki veritabanı
kurallarını uygulama rolünün kendi yetkileriyle dener. Her kural, ihlal
edildiğinde beklenen kısıtın adıyla reddedildiği gösterilerek test edilir.
Böylece isimlendirme kuralının ürettiği adlar da doğrulanmış olur. Testlerin
yaptığı her değişiklik app_connection tarafından geri alınır.

description: Kuruluş planının ikinci adımındaki tabloların veritabanı kurallarını test eder.
"""

import psycopg
import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import DBAPIError

INSERT_CURRENCY = "INSERT INTO currency (code, name, symbol, decimals) VALUES (:code, 'Deneme', 'D', :decimals)"
INSERT_RATE = (
    "INSERT INTO exchange_rate (currency_id, rate_date, buying, selling, source) "
    "VALUES ((SELECT id FROM currency WHERE code = 'USD'), :day, :buying, :selling, 'manual')"
)
INSERT_COMPANY = (
    "INSERT INTO company (name, legal_name, tax_number, tax_office, currency_id) "
    "VALUES (:name, 'Deneme Ltd. Şti.', :tax_number, 'Kadıköy', "
    "COALESCE(:currency_id, (SELECT id FROM currency WHERE code = 'TRY')))"
)
INSERT_USER = "INSERT INTO app_user (email, full_name, password_hash) VALUES (:email, 'Deneme', 'x')"

# PostgreSQL'in hata kodları. Kısıt ihlallerinde hangi kısıtın ihlal edildiği
# ayrıca kontrol edildiği için burada sadece kısıt adı taşımayan hatalar var.
INSUFFICIENT_PRIVILEGE = "42501"
GENERATED_ALWAYS = "428C9"
VALUE_TOO_LONG = "22001"


# Komut bir savepoint içinde çalıştırılır. Hata veren bir komut bütün
# transaction'ı geçersiz kılardı, savepoint sadece kendisini geri alır ve
# aynı testte sonraki komutlar çalışmaya devam edebilir.
def _rejected(connection: Connection, sql: str, params: dict | None = None) -> psycopg.Error:
    with pytest.raises(DBAPIError) as error:
        with connection.begin_nested():
            connection.execute(text(sql), params or {})
    return error.value.orig


# Kısıt ihlallerinde PostgreSQL ihlal edilen kısıtın adını hatanın ayrıntısında
# verir, testler hata metnine değil bu ada bakar.
def _violated_constraint(connection: Connection, sql: str, params: dict | None = None) -> str:
    return _rejected(connection, sql, params).diag.constraint_name


# --- Para birimleri ---

def test_currencies_are_seeded(app_connection: Connection) -> None:
    codes = app_connection.execute(text("SELECT code FROM currency ORDER BY code")).scalars().all()
    assert codes == ["EUR", "TRY", "USD"]


@pytest.mark.parametrize(
    ("code", "decimals", "constraint"),
    [
        ("usd", 2, "ck_currency_code_format"),
        ("US", 2, "ck_currency_code_format"),
        ("GBP", 3, "ck_currency_decimals_range"),
        ("TRY", 2, "uq_currency_code"),
    ],
)
def test_currency_rules(app_connection: Connection, code: str, decimals: int, constraint: str) -> None:
    params = {"code": code, "decimals": decimals}
    assert _violated_constraint(app_connection, INSERT_CURRENCY, params) == constraint


# Bir satıra id elle verilemez, id'yi her zaman veritabanı üretir.
def test_id_cannot_be_given(app_connection: Connection) -> None:
    sql = "INSERT INTO currency (id, code, name, symbol) VALUES (999, 'GBP', 'Sterlin', '£')"
    assert _rejected(app_connection, sql).sqlstate == GENERATED_ALWAYS


# set_updated_at tetikleyicisinin tabloya gerçekten bağlandığını gösterir.
# updated_at'e elle eski bir tarih yazılsa bile tetikleyici onu o anın
# zamanıyla ezer. now() transaction'ın başladığı anı verdiği için eşitlik birebir.
def test_updated_at_is_set_on_update(app_connection: Connection) -> None:
    app_connection.execute(text("UPDATE currency SET updated_at = '2000-01-01' WHERE code = 'USD'"))
    is_now = app_connection.execute(text("SELECT updated_at = now() FROM currency WHERE code = 'USD'")).scalar_one()
    assert is_now


# --- Kurlar ---

@pytest.mark.parametrize(
    ("buying", "selling", "constraint"),
    [
        (0, 1, "ck_exchange_rate_buying_positive"),
        (-1, 1, "ck_exchange_rate_buying_positive"),
        (35, 34.99, "ck_exchange_rate_selling_not_below_buying"),
    ],
)
def test_exchange_rate_amounts(app_connection: Connection, buying: float, selling: float, constraint: str) -> None:
    params = {"day": "2026-10-22", "buying": buying, "selling": selling}
    assert _violated_constraint(app_connection, INSERT_RATE, params) == constraint


def test_exchange_rate_one_per_day(app_connection: Connection) -> None:
    params = {"day": "2026-10-22", "buying": 34.1, "selling": 34.2}
    app_connection.execute(text(INSERT_RATE), params)
    assert _violated_constraint(app_connection, INSERT_RATE, params) == "uq_exchange_rate_currency_id_rate_date"


# --- Şirket ---

@pytest.mark.parametrize("tax_number", ["123456789", "12345678AB"])
def test_company_tax_number_format(app_connection: Connection, tax_number: str) -> None:
    params = {"name": "Deneme", "tax_number": tax_number, "currency_id": None}
    assert _violated_constraint(app_connection, INSERT_COMPANY, params) == "ck_company_tax_number_format"


# On iki haneli bir numara check kısıtına gelmeden varchar(11) sınırına
# takılır. Bu yüzden ihlal edilen bir kısıt adı yoktur, hata koduna bakılır.
def test_company_tax_number_length(app_connection: Connection) -> None:
    params = {"name": "Deneme", "tax_number": "123456789012", "currency_id": None}
    assert _rejected(app_connection, INSERT_COMPANY, params).sqlstate == VALUE_TOO_LONG


def test_company_name_and_tax_number_are_unique(app_connection: Connection) -> None:
    app_connection.execute(text(INSERT_COMPANY), {"name": "Deneme", "tax_number": "1234567890", "currency_id": None})

    same_tax_number = {"name": "Başka", "tax_number": "1234567890", "currency_id": None}
    same_name = {"name": "Deneme", "tax_number": "9876543210", "currency_id": None}
    assert _violated_constraint(app_connection, INSERT_COMPANY, same_tax_number) == "uq_company_tax_number"
    assert _violated_constraint(app_connection, INSERT_COMPANY, same_name) == "uq_company_name"


def test_company_needs_existing_currency(app_connection: Connection) -> None:
    params = {"name": "Deneme", "tax_number": "1234567890", "currency_id": -1}
    assert _violated_constraint(app_connection, INSERT_COMPANY, params) == "fk_company_currency_id_currency"


# RESTRICT: bir şirketin kullandığı para birimi silinemez.
def test_currency_in_use_cannot_be_deleted(app_connection: Connection) -> None:
    app_connection.execute(text(INSERT_COMPANY), {"name": "Deneme", "tax_number": "1234567890", "currency_id": None})
    sql = "DELETE FROM currency WHERE code = 'TRY'"
    assert _violated_constraint(app_connection, sql) == "fk_company_currency_id_currency"


# --- Kullanıcı ---

def test_app_user_email_is_unique_ignoring_case(app_connection: Connection) -> None:
    app_connection.execute(text(INSERT_USER), {"email": "Ali@ornek.com"})
    assert _violated_constraint(app_connection, INSERT_USER, {"email": "ali@ORNEK.com"}) == "ix_app_user_email_lower"


@pytest.mark.parametrize("email", ["ali", "ali@", "@ornek.com", "ali veli@ornek.com"])
def test_app_user_email_format(app_connection: Connection, email: str) -> None:
    assert _violated_constraint(app_connection, INSERT_USER, {"email": email}) == "ck_app_user_email_format"


# --- Yetkiler ---

# Uygulama rolü satır okuyup yazabilir ama şemaya ve Alembic'in sürüm
# tablosuna dokunamaz.
@pytest.mark.parametrize(
    "sql",
    [
        "CREATE TABLE deneme (id int)",
        "DROP TABLE currency",
        "TRUNCATE currency",
        "SELECT * FROM alembic.alembic_version",
    ],
)
def test_app_role_cannot_change_schema(app_connection: Connection, sql: str) -> None:
    assert _rejected(app_connection, sql).sqlstate == INSUFFICIENT_PRIVILEGE
