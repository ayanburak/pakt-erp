"""
file: database.py
importable: Base, AuditMixin, NAMING_CONVENTION, create_database_engine, create_session_factory

Bütün SQLAlchemy tabloları Base'den türetilir. Base her tabloya veritabanının
ürettiği bir id verir. Base.metadata, Alembic'in şemayı karşılaştırırken
baktığı tablo listesidir, bir tablonun bu listeye girmesi için modülünün
Alembic çalışmadan önce import edilmiş olması gerekir. AuditMixin'i miras alan
tablo, kaydı kimin ve ne zaman oluşturup değiştirdiğini tutan dört sütun
kazanır. Böyle bir tablonun migration'ında set_updated_at tetikleyicisinin de
kurulması gerekir, yoksa updated_at güncellenmez. Uygulama veritabanına
create_database_engine ile kurulan engine ve create_session_factory ile
kurulan oturum üreticisi üzerinden bağlanır.

description: Tabloların ortak tabanını, kısıt isimlendirme kuralını ve uygulamanın veritabanı bağlantısını tanımlar.
"""

# NOTE: AuditMixin app_user tablosunu adıyla gösterir. Yani bu altyapı
# dosyası identity modülünün tablo adına bağlıdır, app_user'ın adı
# değişirse burası da değişmeli.

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, MetaData, func
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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


# type_annotation_map, Mapped[int] yazılan her sütunun bigint, Mapped[datetime]
# yazılan her sütunun saat dilimli zaman olmasını sağlar. Böylece bunlar her
# sütunda ayrıca yazılmaz. Daha küçük bir tür gereken sütunda tür elle verilir.
# id GENERATED ALWAYS ile üretilir, id'yi dışarıdan vermeye çalışan bir
# INSERT hata verir. sort_order id'yi her tabloda ilk sütun yapar.
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {
        int: BigInteger,
        datetime: DateTime(timezone=True),
    }

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True, sort_order=-1)


# Zamanları veritabanı doldurur: created_at varsayılan değerle, updated_at
# set_updated_at tetikleyicisiyle. Kim sütunlarını uygulama doldurur. Boş
# olabilirler, çünkü migration'ın yüklediği kayıtların bir kullanıcısı yoktur.
# Bu sütunlara index konmadı, bir kullanıcının kayıtlarını listeleme ihtiyacı
# doğarsa eklenir. sort_order dört sütunu her tabloda en sona koyar.
class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), sort_order=100)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"), sort_order=101)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), sort_order=102)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"), sort_order=103)


# --- Bağlantı ---

# pool_pre_ping, havuzdan alınan bağlantıyı kullanmadan önce yoklar. Sunucu
# yeniden başlatılmışsa kopmuş bir bağlantı isteğe hata olarak yansımaz,
# sessizce yenisiyle değiştirilir.
def create_database_engine(url: str) -> AsyncEngine:
    """Uygulamanın asenkron engine'ini kurar.

    Args:
        url: postgresql+psycopg ile başlayan bağlantı adresi.

    Returns:
        Bağlantı havuzunu yöneten engine. Uygulama kapanırken dispose() ile kapatılmalı.
    """
    return create_async_engine(url, pool_pre_ping=True)


# expire_on_commit=False olmadan commit'ten sonra nesnelerin alanlarına
# erişmek veritabanına yeni bir sorgu atmaya çalışır, asenkron oturumda bu
# hata verir. Repository'ler nesneleri zaten entity'ye çevirip döndürdüğü
# için bu ayarın bir yan etkisi yok.
def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Verilen engine'e bağlı oturum üreticisini kurar.

    Args:
        engine: create_database_engine'in döndürdüğü engine.

    Returns:
        Her çağrıldığında yeni bir AsyncSession açan üretici.
    """
    return async_sessionmaker(engine, expire_on_commit=False)
