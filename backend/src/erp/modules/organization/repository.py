"""
file: repository.py
importable: SqlCompanyRepository

CompanyRepository'nin SQLAlchemy ile yazılmış hali. Kendi transaction'ını
açmaz ve commit etmez, verilen oturumun transaction'ı içinde çalışır.
Transaction'ın sınırını çağıran taraf, uygulamada her HTTP isteği belirler.

description: Şirket kayıtlarını PostgreSQL'de saklayan repository.
"""

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from erp.modules.organization import models
from erp.modules.organization.entities import Company, NewCompany
from erp.modules.organization.errors import CompanyNameTaken, TaxNumberTaken, UnknownCurrency
from erp.modules.organization.ports import CompanyRepository
from erp.shared.errors import DomainError

# Veritabanının reddettiği kısıtın adı hangi iş hatasına karşılık geliyor.
# Adlar isimlendirme kuralından gelir, kural değişirse burası da değişmeli.
CONSTRAINT_ERRORS: dict[str, type[DomainError]] = {
    "uq_company_name": CompanyNameTaken,
    "uq_company_tax_number": TaxNumberTaken,
    "fk_company_currency_id_currency": UnknownCurrency,
}


class SqlCompanyRepository(CompanyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Kayıt önceden "bu numara var mı" diye sorulmadan eklenir. Sorup sonra
    # eklemek, aynı anda gelen iki isteğin ikisinin de yok cevabını almasına
    # açıktır, kısıtı ise veritabanı her durumda tek başına uygular. flush bir
    # savepoint içinde yapılır, böylece reddedilen ekleme sadece kendisini
    # geri alır ve oturumun dış transaction'ı kullanılabilir kalır.
    async def add(self, company: NewCompany) -> Company:
        row = models.Company(**asdict(company))
        try:
            async with self._session.begin_nested():
                self._session.add(row)
                await self._session.flush()
        except IntegrityError as error:
            raise _translate(error) from error
        return _to_entity(row)

    async def get(self, company_id: int) -> Company | None:
        row = await self._session.get(models.Company, company_id)
        return _to_entity(row) if row else None

    async def list_all(self) -> list[Company]:
        rows = await self._session.scalars(select(models.Company).order_by(models.Company.id))
        return [_to_entity(row) for row in rows]


# Tanınmayan bir kısıt ihlali iş hatasına çevrilmez, olduğu gibi geri
# döndürülür. Bu bir programlama hatasına işaret eder ve kullanıcıya genel
# bir hata olarak yansımalı.
def _translate(error: IntegrityError) -> Exception:
    diag = getattr(error.orig, "diag", None)
    domain_error = CONSTRAINT_ERRORS.get(getattr(diag, "constraint_name", None) or "")
    return domain_error() if domain_error else error


def _to_entity(row: models.Company) -> Company:
    return Company(
        id=row.id,
        name=row.name,
        legal_name=row.legal_name,
        tax_number=row.tax_number,
        tax_office=row.tax_office,
        currency_id=row.currency_id,
        created_at=row.created_at,
    )
