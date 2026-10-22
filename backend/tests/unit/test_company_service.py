"""
file: test_company_service.py

CompanyService'i veritabanı olmadan, bellekte çalışan sahte bir repository
ile dener. Servisin sadece CompanyRepository soyut sınıfını tanıdığını ve
yerine başka bir sınıf geçebildiğini de göstermiş olur.

description: CompanyService'in birim testleri.
"""

from dataclasses import asdict
from datetime import UTC, datetime

import pytest

from erp.modules.organization.entities import Company, NewCompany
from erp.modules.organization.errors import CompanyNotFound, InvalidTaxNumber, TaxNumberTaken
from erp.modules.organization.ports import CompanyRepository
from erp.modules.organization.service import CompanyService

pytestmark = pytest.mark.anyio


# Sadece servisin kullandığı davranışı taklit eder. Benzersizlikten yalnızca
# vergi numarası kontrol edilir, bu testler için yeterli.
class FakeCompanyRepository(CompanyRepository):
    def __init__(self) -> None:
        self.companies: dict[int, Company] = {}

    async def add(self, company: NewCompany) -> Company:
        if any(c.tax_number == company.tax_number for c in self.companies.values()):
            raise TaxNumberTaken()
        saved = Company(id=len(self.companies) + 1, created_at=datetime.now(UTC), **asdict(company))
        self.companies[saved.id] = saved
        return saved

    async def get(self, company_id: int) -> Company | None:
        return self.companies.get(company_id)

    async def list_all(self) -> list[Company]:
        return list(self.companies.values())


def new_company(tax_number: str = "1234567890") -> NewCompany:
    return NewCompany(name="Deneme", legal_name="Deneme Ltd.", tax_number=tax_number, tax_office="Kadıköy", currency_id=1)


@pytest.fixture
def repository() -> FakeCompanyRepository:
    return FakeCompanyRepository()


@pytest.fixture
def service(repository: FakeCompanyRepository) -> CompanyService:
    return CompanyService(repository)


async def test_create_saves_company(service: CompanyService, repository: FakeCompanyRepository) -> None:
    company = await service.create(new_company())
    assert company.id == 1
    assert repository.companies[1].tax_number == "1234567890"


# Kontrol hanesi tutmayan numara repository'ye hiç ulaşmamalı.
async def test_create_rejects_invalid_tax_number(service: CompanyService, repository: FakeCompanyRepository) -> None:
    with pytest.raises(InvalidTaxNumber):
        await service.create(new_company(tax_number="1234567891"))
    assert repository.companies == {}


# Repository'nin fırlattığı iş hatası servisten değişmeden geçmeli.
async def test_create_passes_repository_errors(service: CompanyService) -> None:
    await service.create(new_company())
    with pytest.raises(TaxNumberTaken):
        await service.create(new_company())


async def test_get_missing_company(service: CompanyService) -> None:
    with pytest.raises(CompanyNotFound):
        await service.get(42)
