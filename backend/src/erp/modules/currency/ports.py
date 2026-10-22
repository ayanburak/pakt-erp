"""
file: ports.py
importable: CurrencyRepository

Servisin para birimlerine erişmek için ihtiyaç duyduğu soyut sınıf.

description: currency modülünün veri erişimi için soyut sınıfını tanımlar.
"""

from abc import ABC, abstractmethod

from erp.modules.currency.entities import Currency


class CurrencyRepository(ABC):
    """Para birimlerini okuyan depo."""

    @abstractmethod
    async def list_all(self) -> list[Currency]:
        """Bütün para birimlerini id sırasıyla döndürür."""
