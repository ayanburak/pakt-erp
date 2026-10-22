"""
set_updated_at

Revision ID: 51ba9698bfc2
Revises:
Create Date: 2026-10-22 03:13:18.053789
"""

# set_updated_at(), updated_at sütunu olan her tabloda BEFORE UPDATE
# tetikleyicisi olarak kullanılmak için kurulur. Bir satır güncellendiğinde
# updated_at'i uygulama yazmasa bile o anın zamanıyla doldurur. now()
# transaction'ın başladığı anı verir, aynı transaction'da güncellenen
# satırların hepsi aynı zamanı alır. Fonksiyon tabloların sahibine aittir,
# PostgreSQL fonksiyonlara varsayılan olarak herkese çalıştırma izni verdiği
# için uygulama rolüne ayrıca yetki gerekmez.

from collections.abc import Sequence

from alembic import op

revision: str = '51ba9698bfc2'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE FUNCTION set_updated_at() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at := now();
            RETURN NEW;
        END
        $$
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION set_updated_at()")
