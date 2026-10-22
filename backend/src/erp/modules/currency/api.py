"""
file: api.py
importable: router

Para birimi uç noktaları.

description: currency modülünün HTTP uç noktalarını tanımlar.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from erp.modules.currency.repository import SqlCurrencyRepository
from erp.modules.currency.schemas import CurrencyRead
from erp.modules.currency.service import CurrencyService
from erp.web.dependencies import SessionDep

router = APIRouter(prefix="/currencies", tags=["Para birimleri"])


# Servisin hangi repository ile kurulacağına burada karar verilir.
def get_currency_service(session: SessionDep) -> CurrencyService:
    return CurrencyService(SqlCurrencyRepository(session))


ServiceDep = Annotated[CurrencyService, Depends(get_currency_service)]


@router.get("", summary="Para birimlerini listele")
async def list_currencies(service: ServiceDep) -> list[CurrencyRead]:
    return [CurrencyRead.model_validate(currency) for currency in await service.list_all()]
