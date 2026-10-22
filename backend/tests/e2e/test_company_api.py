"""
file: test_company_api.py

Para birimi ve şirket uç noktalarını gerçek HTTP istekleriyle dener. İstekler
uygulamanın kendi transaction düzeniyle çalışır ve gerçekten commit eder.
Cevap kodları ve Türkçe hata mesajları birlikte kontrol edilir.

description: Şirket ve para birimi uç noktalarının uçtan uca testleri.
"""

import httpx
import pytest

pytestmark = pytest.mark.anyio

VALID_COMPANY = {
    "name": "Pakt Deneme",
    "legal_name": "Pakt Deneme Yazılım Ltd. Şti.",
    "tax_number": "1234567890",
    "tax_office": "Kadıköy",
    "currency_id": 1,
}


async def test_list_currencies(client: httpx.AsyncClient) -> None:
    response = await client.get("/currencies")
    assert response.status_code == 200
    assert [c["code"] for c in response.json()] == ["TRY", "USD", "EUR"]


async def test_create_and_read_company(client: httpx.AsyncClient) -> None:
    created = await client.post("/companies", json=VALID_COMPANY)
    assert created.status_code == 201
    body = created.json()
    assert {k: body[k] for k in VALID_COMPANY} == VALID_COMPANY

    fetched = await client.get(f"/companies/{body['id']}")
    assert fetched.json() == body
    assert (await client.get("/companies")).json() == [body]


# Reddedilen istek kendi transaction'ını geri alır, veritabanında yarım bir
# kayıt kalmaz. Liste hâlâ tek şirket göstermeli.
async def test_duplicate_tax_number(client: httpx.AsyncClient) -> None:
    await client.post("/companies", json=VALID_COMPANY)
    response = await client.post("/companies", json=VALID_COMPANY | {"name": "Başka"})
    assert response.status_code == 409
    assert response.json() == {"detail": "Bu vergi numarasıyla kayıtlı bir şirket var."}
    assert len((await client.get("/companies")).json()) == 1


@pytest.mark.parametrize(
    ("change", "detail"),
    [
        ({"tax_number": "1234567891"}, "Vergi numarası geçersiz."),
        ({"currency_id": 999}, "Para birimi bulunamadı."),
    ],
)
async def test_business_rule_errors(client: httpx.AsyncClient, change: dict, detail: str) -> None:
    response = await client.post("/companies", json=VALID_COMPANY | change)
    assert response.status_code == 422
    assert response.json() == {"detail": detail}


async def test_validation_errors_are_turkish(client: httpx.AsyncClient) -> None:
    payload = VALID_COMPANY | {"name": "   ", "tax_number": "12ab"}
    del payload["tax_office"]
    response = await client.post("/companies", json=payload)
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Girilen bilgiler geçersiz.",
        "errors": [
            {"field": "name", "message": "En az 1 karakter olmalı."},
            {"field": "tax_number", "message": "Biçimi geçersiz."},
            {"field": "tax_office", "message": "Bu alan zorunlu."},
        ],
    }


@pytest.mark.parametrize(
    ("path", "status", "detail"),
    [
        ("/companies/999", 404, "Şirket bulunamadı."),
        ("/yok", 404, "Adres bulunamadı."),
    ],
)
async def test_not_found(client: httpx.AsyncClient, path: str, status: int, detail: str) -> None:
    response = await client.get(path)
    assert response.status_code == status
    assert response.json() == {"detail": detail}
