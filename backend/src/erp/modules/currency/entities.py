"""
file: entities.py
importable: Currency

Servisin gördüğü para birimi nesnesi. SQLAlchemy'den ve FastAPI'den
bağımsızdır ve değiştirilemez.

description: currency modülünün servis katmanında kullanılan veri sınıflarını tanımlar.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Currency:
    id: int
    code: str
    name: str
    symbol: str
    decimals: int
