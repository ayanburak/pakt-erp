"""
file: models.py
importable: Company

Şirket tablosu. currency_id şirketin defterlerinin tutulduğu para birimidir.

description: organization modülünün veritabanı tablolarını tanımlar.
"""

# TODO: Fiş kaydı olan bir şirketin para birimi değiştirilememeli. Bu kural
# fiş tablosu kurulunca, kuruluş planının beşinci adımında bir tetikleyiciyle
# eklenecek.

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from erp.infrastructure.database import AuditMixin, Base


# tax_number tüzel kişide on haneli VKN, şahıs şirketinde on bir haneli
# TCKN'dir. Kısıt sadece hane sayısını ve rakam olmasını denetler, VKN ve
# TCKN'nin kendi kontrol hanesi algoritmaları uygulama katmanında denetlenecek.
class Company(AuditMixin, Base):
    __tablename__ = "company"
    __table_args__ = (
        CheckConstraint("tax_number ~ '^[0-9]{10,11}$'", name="tax_number_format"),
    )

    name: Mapped[str] = mapped_column(String(100), unique=True)
    legal_name: Mapped[str] = mapped_column(String(250))
    tax_number: Mapped[str] = mapped_column(String(11), unique=True)
    tax_office: Mapped[str] = mapped_column(String(100))
    currency_id: Mapped[int] = mapped_column(ForeignKey("currency.id", ondelete="RESTRICT"), index=True)
