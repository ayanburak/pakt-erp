"""
file: service.py
importable: CompanyService

Şirketlerle ilgili iş kuralları. Servis FastAPI'yi ve SQLAlchemy'yi bilmez,
verilere sadece kendisine verilen CompanyRepository üzerinden erişir. Hata
durumlarında erp.shared.errors türlerinden türeyen iş hataları fırlatır.

description: Şirket açma, getirme ve listeleme iş kurallarını uygulayan servis.
"""

from erp.modules.organization.entities import Company, NewCompany
from erp.modules.organization.errors import CompanyNotFound, InvalidTaxNumber
from erp.modules.organization.ports import CompanyRepository
from erp.modules.organization.tax_number import is_valid_tax_number


# Repository dışarıdan verilir, servis onu kendisi oluşturmaz. Uygulamada
# SqlCompanyRepository, testlerde bellekte çalışan sahte bir repository verilir.
class CompanyService:
    """Şirketlerle ilgili iş kurallarını uygular.

    Args:
        repository: Şirket kayıtlarına erişilecek depo.
    """

    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    # Hane sayısı ve rakam kontrolü daha önce istek katmanında yapılmış olsa
    # bile kontrol hanesi burada denetlenir. Bu bir iş kuralıdır, şirketi
    # HTTP dışında bir yoldan açan bir çağrı da bu kurala takılmalı.
    async def create(self, company: NewCompany) -> Company:
        """Yeni bir şirket açar.

        Args:
            company: Açılacak şirketin bilgileri.

        Returns:
            Kaydedilmiş şirket.

        Raises:
            InvalidTaxNumber: Vergi numarasının kontrol hanesi tutmuyorsa.
            CompanyNameTaken: Aynı adla bir şirket varsa.
            TaxNumberTaken: Aynı vergi numarasıyla bir şirket varsa.
            UnknownCurrency: Para birimi yoksa.
        """
        if not is_valid_tax_number(company.tax_number):
            raise InvalidTaxNumber()
        return await self._repository.add(company)

    async def get(self, company_id: int) -> Company:
        """id'si verilen şirketi döndürür.

        Raises:
            CompanyNotFound: Böyle bir şirket yoksa.
        """
        company = await self._repository.get(company_id)
        if company is None:
            raise CompanyNotFound()
        return company

    async def list_all(self) -> list[Company]:
        """Bütün şirketleri id sırasıyla döndürür."""
        return await self._repository.list_all()
