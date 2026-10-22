"""
file: schemas.py
importable: CompanyCreate, CompanyRead

Şirket uç noktalarının istek ve cevap biçimleri. Burada sadece biçim
denetlenir: uzunluk, rakam ve zorunluluk. Vergi numarasının kontrol hanesi
gibi iş kuralları serviste denetlenir. Açıklamalar ve örnekler /docs
sayfasında görünür.

description: organization modülünün HTTP istek ve cevap şemalarını tanımlar.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Metin alanlarının başındaki ve sonundaki boşluklar silinir, sadece
# boşluktan oluşan bir ad böylece boş sayılır ve min_length'e takılır.
class CompanyCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100, description="Kısa ad", examples=["Pakt Deneme"])
    legal_name: str = Field(
        min_length=1, max_length=250, description="Ticaret unvanı", examples=["Pakt Deneme Yazılım Ltd. Şti."]
    )
    tax_number: str = Field(
        pattern=r"^[0-9]{10,11}$", description="On haneli VKN ya da on bir haneli TCKN", examples=["1234567890"]
    )
    tax_office: str = Field(min_length=1, max_length=100, description="Vergi dairesi", examples=["Kadıköy"])
    currency_id: int = Field(gt=0, description="Defterin para birimi, GET /currencies'ten", examples=[1])


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    legal_name: str
    tax_number: str
    tax_office: str
    currency_id: int
    created_at: datetime
