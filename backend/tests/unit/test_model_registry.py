"""
file: test_model_registry.py

Uygulama tek başına çalıştığında bütün tabloların Base.metadata'ya girdiğini
doğrular. Bir yabancı anahtarın gösterdiği tablo listede yoksa SQLAlchemy
kayıt yazarken NoReferencedTableError fırlatır.

description: Uygulamanın kendi import'larıyla bütün modelleri kaydettiğini test eder.
"""

import subprocess
import sys

# Kontrol ayrı bir Python işleminde yapılır. Aynı işlemde başka testler,
# örneğin Alembic'i çalıştıranlar, modelleri önceden import etmiş olabilir ve
# eksik bir import'u gizler. Bu hata ilk kez tam böyle gizlenmişti: env.py
# identity'nin modelini import ediyordu, main.py etmiyordu.
CHECK = """
import erp.main
from erp.infrastructure.database import Base

for table in Base.metadata.tables.values():
    for key in table.foreign_keys:
        key.column
"""


def test_app_registers_all_referenced_tables() -> None:
    result = subprocess.run([sys.executable, "-c", CHECK], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
