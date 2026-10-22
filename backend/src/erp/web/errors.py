"""
file: errors.py
importable: register_error_handlers, ErrorResponse, ValidationErrorResponse

Uygulamanın bütün hata cevaplarını Türkçe ve tek biçimde verir. İş hataları
türlerine göre HTTP koduna çevrilir. Pydantic'in İngilizce doğrulama
mesajları Türkçeye çevrilir ve hangi alanda olduklarıyla birlikte listelenir.
Beklenmeyen bir hata kullanıcıya ayrıntısı gösterilmeden 500 olarak döner,
ayrıntısı loga yazılır.

description: Hataları Türkçe HTTP cevaplarına çeviren işleyicileri tanımlar.
"""

# TODO: Pydantic'in hata türlerinin sadece en sık karşılaşılanları çevrildi.
# Çevrilmeyen bir tür VALIDATION_MESSAGES'ta yoksa genel bir mesaj gösterilir,
# yeni bir alan türü eklendiğinde bu liste gözden geçirilmeli.

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from erp.shared.errors import Conflict, DomainError, InvalidInput, NotFound

logger = logging.getLogger(__name__)

# Sıra önemli değil, bir hata bu türlerden yalnızca birinden türer.
STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFound: 404,
    Conflict: 409,
    InvalidInput: 422,
}

# Mesajlardaki süslü parantezli yerler Pydantic'in hatayla birlikte verdiği
# ctx sözlüğünden doldurulur, örneğin max_length.
VALIDATION_MESSAGES = {
    "missing": "Bu alan zorunlu.",
    "string_type": "Metin olmalı.",
    "string_too_short": "En az {min_length} karakter olmalı.",
    "string_too_long": "En fazla {max_length} karakter olabilir.",
    "string_pattern_mismatch": "Biçimi geçersiz.",
    "int_type": "Tam sayı olmalı.",
    "int_parsing": "Tam sayı olmalı.",
    "greater_than": "{gt} sayısından büyük olmalı.",
    "json_invalid": "İstek gövdesi geçerli bir JSON değil.",
    "model_attributes_type": "Bir nesne olmalı.",
}

HTTP_MESSAGES = {
    404: "Adres bulunamadı.",
    405: "Bu adres bu yöntemi desteklemiyor.",
}


class ErrorResponse(BaseModel):
    detail: str


class FieldError(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    detail: str
    errors: list[FieldError]


def register_error_handlers(app: FastAPI) -> None:
    """Uygulamaya hata işleyicilerini ekler.

    Args:
        app: İşleyicilerin ekleneceği uygulama.
    """
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected_error)


# Hata, türlerden hiçbirinden türemiyorsa iş kuralı ihlali sayılır ve 400 döner.
async def _domain_error(request: Request, error: DomainError) -> JSONResponse:
    status = next((code for kind, code in STATUS_BY_ERROR.items() if isinstance(error, kind)), 400)
    return JSONResponse(status_code=status, content={"detail": error.message})


async def _validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    errors = [{"field": _field_name(item["loc"]), "message": _translate(item)} for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": "Girilen bilgiler geçersiz.", "errors": errors})


# Konumun ilk parçası verinin nereden geldiğini söyler, body, path ya da
# query. Kullanıcı için anlamı olmadığı için atılır, alan adı kalır.
def _field_name(location: tuple) -> str:
    return ".".join(str(part) for part in location[1:]) or str(location[0])


def _translate(item: dict) -> str:
    template = VALIDATION_MESSAGES.get(item["type"], "Değer geçersiz.")
    return template.format(**item.get("ctx", {}))


# FastAPI'nin kendisinin ürettiği hatalar, örneğin tanımsız bir adres.
async def _http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
    message = HTTP_MESSAGES.get(error.status_code, "İstek işlenemedi.")
    return JSONResponse(status_code=error.status_code, content={"detail": message}, headers=error.headers)


# Ayrıntı kullanıcıya gösterilmez, çünkü veritabanı adı ya da SQL gibi iç
# bilgiler içerebilir. Ayrıntı loga yazılır.
async def _unexpected_error(request: Request, error: Exception) -> JSONResponse:
    logger.exception("Beklenmeyen hata: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Beklenmeyen bir hata oluştu."})
