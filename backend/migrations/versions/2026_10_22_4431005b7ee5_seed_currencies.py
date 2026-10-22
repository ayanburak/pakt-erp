"""
seed_currencies

Revision ID: 4431005b7ee5
Revises: d676b9d2e40f
Create Date: 2026-10-22 03:31:05.780836
"""

# Kuruluş planının ikinci adımının istediği üç para birimini yükler. Tablo
# modelden import edilmez, sadece gereken sütunlarla burada tanımlanır.
# Model ileride değişse bile bu migration yazıldığı günkü şemayla çalışmaya
# devam eder. Downgrade sadece bu üç kaydı siler. Bu para birimlerinden birini
# kullanan bir kur ya da şirket varsa RESTRICT yüzünden silme hata verir, bu
# bilinçli bir durumdur, veri kaybı yerine downgrade durur.

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '4431005b7ee5'
down_revision: str | Sequence[str] | None = 'd676b9d2e40f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENCIES = [
    {"code": "TRY", "name": "Türk lirası", "symbol": "₺", "decimals": 2},
    {"code": "USD", "name": "ABD doları", "symbol": "$", "decimals": 2},
    {"code": "EUR", "name": "Euro", "symbol": "€", "decimals": 2},
]

currency = sa.table(
    "currency",
    sa.column("code", sa.CHAR(3)),
    sa.column("name", sa.String),
    sa.column("symbol", sa.String),
    sa.column("decimals", sa.SmallInteger),
)


def upgrade() -> None:
    op.bulk_insert(currency, CURRENCIES)


def downgrade() -> None:
    codes = [row["code"] for row in CURRENCIES]
    op.execute(currency.delete().where(currency.c.code.in_(codes)))
