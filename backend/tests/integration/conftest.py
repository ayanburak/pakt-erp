"""
file: conftest.py

Bu klasördeki her test başlamadan önce test veritabanının sıfırlanıp en son
sürüme getirilmesini ister.

description: Entegrasyon testlerini test veritabanına bağlayan ortak ayar.
"""

import pytest


@pytest.fixture(autouse=True)
def _database(fresh_database: None) -> None:
    pass
