"""
file: service.py
importable: CurrencyService

Para birimleriyle ilgili iş kuralları. Şimdilik sadece listeleme var.

description: Para birimlerini listeleyen servis.
"""

from erp.modules.currency.entities import Currency
from erp.modules.currency.ports import CurrencyRepository


# Servis şimdilik isteği repository'ye aktarmaktan başka bir şey yapmıyor.
# Yine de uç nokta repository'yi doğrudan çağırmaz, kur çekme gibi iş
# kuralları geldiğinde yerleri burası olacak.
class CurrencyService:
    """Para birimleriyle ilgili iş kurallarını uygular.

    Args:
        repository: Para birimlerine erişilecek depo.
    """

    def __init__(self, repository: CurrencyRepository) -> None:
        self._repository = repository

    async def list_all(self) -> list[Currency]:
        """Bütün para birimlerini id sırasıyla döndürür."""
        return await self._repository.list_all()
