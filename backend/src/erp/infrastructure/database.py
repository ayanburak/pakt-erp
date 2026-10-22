"""
file: database.py
importable: Base, NAMING_CONVENTION

Bütün SQLAlchemy tabloları Base'den türetilir. Base.metadata, Alembic'in
şemayı karşılaştırırken baktığı tablo listesidir. Bir tablonun bu listeye
girmesi için modülünün Alembic çalışmadan önce import edilmiş olması gerekir.

description: Bütün tabloların ortak tabanını ve kısıt isimlendirme kuralını tanımlar.
"""

# TODO: Uygulamanın asenkron engine'i ve oturum üreticisi ilk repository ile
# birlikte bu dosyaya eklenecek.

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Kısıtlara isim PostgreSQL'e bırakılmaz. Bir migration bir kısıtı silmek ya
# da değiştirmek istediğinde adını önceden bilebilsin diye her kısıt türü
# tablo ve sütun adından türeyen sabit bir isim alır, örneğin pk_currency,
# uq_currency_code, fk_exchange_rate_currency_id_currency. Bu kural ilk
# tablodan sonra değiştirilirse var olan bütün kısıtların yeniden
# adlandırılması gerekir. ck için isim her check kısıtında elle verilir,
# çünkü bir check ifadesinden anlamlı bir isim türetilemez. PostgreSQL
# isimleri 63 karakterde keser, bu sınırı aşan bir isim SQLAlchemy tarafından
# kısaltılıp sonuna kısa bir özet eklenir.
NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}


# Kurala uyulması için metadata'nın Base üzerinde bir kere tanımlanması
# yeterli, Base'den türeyen her tablo aynı metadata'yı paylaşır.
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
