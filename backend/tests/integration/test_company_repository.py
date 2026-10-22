"""
file: test_company_repository.py

SqlCompanyRepository'yi test veritabanında, uygulama rolüyle ve asenkron
bağlantıyla dener. Her test tek bir transaction içinde çalışır ve sonunda
geri alınır.

description: SqlCompanyRepository'nin entegrasyon testleri.
"""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from erp.modules.organization.entities import NewCompany
from erp.modules.organization.errors import CompanyNameTaken, TaxNumberTaken, UnknownCurrency
from erp.modules.organization.repository import SqlCompanyRepository

pytestmark = pytest.mark.anyio

TRY_ID = 1


# Oturum dışarıda açılmış bir transaction'a bağlanır. Repository'nin açtığı
# savepoint'ler bu transaction'ın içinde kalır, test bitince hepsi birlikte
# geri alınır.
@pytest.fixture
async def repository(app_url: URL) -> AsyncIterator[SqlCompanyRepository]:
    engine = create_async_engine(app_url)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        yield SqlCompanyRepository(session)
        await session.close()
        await transaction.rollback()
    await engine.dispose()


def new_company(name: str = "Deneme", tax_number: str = "1234567890", currency_id: int = TRY_ID) -> NewCompany:
    return NewCompany(
        name=name, legal_name="Deneme Ltd.", tax_number=tax_number, tax_office="Kadıköy", currency_id=currency_id
    )


# id ve created_at veritabanında üretilir, repository'nin bunları geri
# okuyup entity'ye koyabildiği gösterilir.
async def test_add_returns_saved_company(repository: SqlCompanyRepository) -> None:
    company = await repository.add(new_company())
    assert company.id > 0
    assert company.created_at is not None
    assert await repository.get(company.id) == company


# Her kısıt ihlali kendi iş hatasına çevrilmeli. Reddedilen her ekleme sadece
# kendi savepoint'ini geri aldığı için aynı oturumda sonraki ekleme yine
# çalışabilmeli, testin son satırı bunu gösterir.
async def test_add_translates_constraint_errors(repository: SqlCompanyRepository) -> None:
    await repository.add(new_company())

    with pytest.raises(TaxNumberTaken):
        await repository.add(new_company(name="Başka"))
    with pytest.raises(CompanyNameTaken):
        await repository.add(new_company(tax_number="4540536920"))
    with pytest.raises(UnknownCurrency):
        await repository.add(new_company(name="Başka", tax_number="4540536920", currency_id=999))

    await repository.add(new_company(name="Başka", tax_number="4540536920"))
    assert len(await repository.list_all()) == 2


async def test_get_missing_company(repository: SqlCompanyRepository) -> None:
    assert await repository.get(999) is None
