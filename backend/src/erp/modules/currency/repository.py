"""
file: repository.py
importable: SqlCurrencyRepository

CurrencyRepository'nin SQLAlchemy ile yazılmış hali. Verilen oturumun
transaction'ı içinde çalışır.

description: Para birimlerini PostgreSQL'den okuyan repository.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from erp.modules.currency import models
from erp.modules.currency.entities import Currency
from erp.modules.currency.ports import CurrencyRepository


class SqlCurrencyRepository(CurrencyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Currency]:
        rows = await self._session.scalars(select(models.Currency).order_by(models.Currency.id))
        return [_to_entity(row) for row in rows]


# code sütunu char(3) olduğu için PostgreSQL değeri sağdan boşlukla
# doldurabilir, rstrip bu ihtimale karşı.
def _to_entity(row: models.Currency) -> Currency:
    return Currency(id=row.id, code=row.code.rstrip(), name=row.name, symbol=row.symbol, decimals=row.decimals)
