"""
file: models.py
importable: Currency, ExchangeRate

Para birimlerinin ve TL karşılığı kurlarının tabloları. Kurlar her zaman TL
karşılığıdır, TRY için kur satırı tutulmaz. Bir para biriminin aynı güne
tek bir kuru olur.

description: currency modülünün veritabanı tablolarını tanımlar.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import CHAR, CheckConstraint, ForeignKey, Numeric, SmallInteger, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from erp.infrastructure.database import AuditMixin, Base


# decimals 2'yi geçemez çünkü fiş tutarları numeric(18,2), yani en fazla iki
# kuruş basamağı tutuyor. Kuveyt dinarı gibi üç basamaklı para birimleri bu
# yüzden şimdilik desteklenmiyor.
class Currency(AuditMixin, Base):
    __tablename__ = "currency"
    __table_args__ = (
        CheckConstraint("code ~ '^[A-Z]{3}$'", name="code_format"),
        CheckConstraint("decimals BETWEEN 0 AND 2", name="decimals_range"),
    )

    code: Mapped[str] = mapped_column(CHAR(3), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    symbol: Mapped[str] = mapped_column(String(10))
    decimals: Mapped[int] = mapped_column(SmallInteger, server_default=text("2"))


# currency_id ile rate_date üzerindeki benzersizlik kısıtı currency_id ile
# başlayan bir index de kurar, bu yüzden currency_id'ye ayrıca index konmadı.
# selling'in buying'den küçük olamaması, selling'in de sıfırdan büyük olmasını
# kendiliğinden sağlar.
class ExchangeRate(AuditMixin, Base):
    __tablename__ = "exchange_rate"
    __table_args__ = (
        UniqueConstraint("currency_id", "rate_date"),
        CheckConstraint("buying > 0", name="buying_positive"),
        CheckConstraint("selling >= buying", name="selling_not_below_buying"),
    )

    currency_id: Mapped[int] = mapped_column(ForeignKey("currency.id", ondelete="RESTRICT"))
    rate_date: Mapped[date]
    buying: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    selling: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    source: Mapped[str] = mapped_column(String(50))
