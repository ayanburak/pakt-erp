"""
file: schemas.py
importable: CurrencyRead

Para birimi uç noktalarının cevap biçimi.

description: currency modülünün HTTP cevap şemalarını tanımlar.
"""

from pydantic import BaseModel, ConfigDict


class CurrencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    symbol: str
    decimals: int
