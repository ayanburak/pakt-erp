"""
file: ports.py
importable: CompanyRepository

Servisin şirket kayıtlarına erişmek için ihtiyaç duyduğu soyut sınıf. Servis
sadece bunu tanır. Gerçek uygulamada repository.py'deki SqlCompanyRepository,
testlerde bellekte çalışan sahte bir sınıf bu soyut sınıfın yerine geçer.

description: organization modülünün veri erişimi için soyut sınıfını tanımlar.
"""

from abc import ABC, abstractmethod

from erp.modules.organization.entities import Company, NewCompany


# Benzersizlik ve yabancı anahtar ihlalleri burada iş hatası olarak tanımlanır,
# veritabanı hatası olarak değil. Böylece yerine geçen her sınıf aynı hataları
# fırlatmak zorundadır ve servis hangi sınıfla çalıştığını bilmeden bu
# hatalara güvenebilir.
class CompanyRepository(ABC):
    """Şirket kayıtlarını saklayan ve geri okuyan depo."""

    @abstractmethod
    async def add(self, company: NewCompany) -> Company:
        """Yeni şirketi kaydeder.

        Args:
            company: Kaydedilecek şirket.

        Returns:
            id'si ve oluşturulma zamanı dolmuş şirket.

        Raises:
            CompanyNameTaken: Aynı adla bir şirket varsa.
            TaxNumberTaken: Aynı vergi numarasıyla bir şirket varsa.
            UnknownCurrency: currency_id bir para birimini göstermiyorsa.
        """

    @abstractmethod
    async def get(self, company_id: int) -> Company | None:
        """id'si verilen şirketi döndürür, yoksa None döndürür."""

    @abstractmethod
    async def list_all(self) -> list[Company]:
        """Bütün şirketleri id sırasıyla döndürür."""
