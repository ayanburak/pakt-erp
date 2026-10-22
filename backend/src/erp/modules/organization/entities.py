"""
file: entities.py
importable: NewCompany, Company

Servisin gördüğü şirket nesneleri. SQLAlchemy'den ve FastAPI'den bağımsızdır,
repository veritabanından okuduğunu bunlara çevirir. İkisi de değiştirilemez,
bir alanı değiştirmek yeni bir nesne oluşturmayı gerektirir.

description: organization modülünün servis katmanında kullanılan veri sınıflarını tanımlar.
"""

from dataclasses import dataclass
from datetime import datetime


# Henüz kaydedilmemiş şirket. id ve created_at'i veritabanı üretir, bu yüzden
# bu nesnede yoklar.
@dataclass(frozen=True, slots=True)
class NewCompany:
    name: str
    legal_name: str
    tax_number: str
    tax_office: str
    currency_id: int


@dataclass(frozen=True, slots=True)
class Company:
    id: int
    name: str
    legal_name: str
    tax_number: str
    tax_office: str
    currency_id: int
    created_at: datetime
