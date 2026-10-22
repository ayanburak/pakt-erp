"""
file: api.py
importable: router

Şirket uç noktaları. Uç noktalar isteği şemayla alır, servise entity olarak
verir ve servisin döndürdüğü entity'yi şemaya çevirip döndürür. Hatalar burada
yakalanmaz, servisin fırlattığı iş hatalarını web katmanındaki işleyiciler
HTTP cevabına çevirir.

description: organization modülünün HTTP uç noktalarını tanımlar.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from erp.modules.organization.entities import NewCompany
from erp.modules.organization.repository import SqlCompanyRepository
from erp.modules.organization.schemas import CompanyCreate, CompanyRead
from erp.modules.organization.service import CompanyService
from erp.web.dependencies import SessionDep
from erp.web.errors import ErrorResponse, ValidationErrorResponse

router = APIRouter(prefix="/companies", tags=["Şirketler"])


# Servisin hangi repository ile kurulacağına burada karar verilir. Testler bu
# fonksiyonu app.dependency_overrides ile değiştirerek servise başka bir
# repository verebilir, uç noktalara dokunmadan.
def get_company_service(session: SessionDep) -> CompanyService:
    return CompanyService(SqlCompanyRepository(session))


ServiceDep = Annotated[CompanyService, Depends(get_company_service)]


@router.post(
    "",
    status_code=201,
    summary="Şirket aç",
    responses={409: {"model": ErrorResponse}, 422: {"model": ValidationErrorResponse}},
)
async def create_company(body: CompanyCreate, service: ServiceDep) -> CompanyRead:
    company = await service.create(NewCompany(**body.model_dump()))
    return CompanyRead.model_validate(company)


@router.get("", summary="Şirketleri listele")
async def list_companies(service: ServiceDep) -> list[CompanyRead]:
    return [CompanyRead.model_validate(company) for company in await service.list_all()]


@router.get("/{company_id}", summary="Şirketi getir", responses={404: {"model": ErrorResponse}})
async def get_company(company_id: int, service: ServiceDep) -> CompanyRead:
    return CompanyRead.model_validate(await service.get(company_id))
