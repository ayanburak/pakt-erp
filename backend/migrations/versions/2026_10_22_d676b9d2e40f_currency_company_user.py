"""
currency_company_user

Revision ID: d676b9d2e40f
Revises: 51ba9698bfc2
Create Date: 2026-10-22 03:30:48.187225
"""

# Tablolar autogenerate ile üretildi. Tetikleyiciler elle eklendi, çünkü
# autogenerate tetikleyicileri görmez. AuditMixin'i miras alan her tablonun
# updated_at sütunu, ilk migration'ın kurduğu set_updated_at fonksiyonuyla
# güncellenir. Downgrade'de tetikleyiciler tablolarla birlikte silinir.

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'd676b9d2e40f'
down_revision: str | Sequence[str] | None = '51ba9698bfc2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

AUDITED_TABLES = ("app_user", "currency", "company", "exchange_rate")


def upgrade() -> None:
    op.create_table('app_user',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('full_name', sa.String(length=150), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint("email ~ '^[^@\\s]+@[^@\\s]+$'", name=op.f('ck_app_user_email_format')),
    sa.ForeignKeyConstraint(['created_by'], ['app_user.id'], name=op.f('fk_app_user_created_by_app_user'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['updated_by'], ['app_user.id'], name=op.f('fk_app_user_updated_by_app_user'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_app_user'))
    )
    op.create_index('ix_app_user_email_lower', 'app_user', [sa.literal_column('lower(email)')], unique=True)
    op.create_table('currency',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('code', sa.CHAR(length=3), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('symbol', sa.String(length=10), nullable=False),
    sa.Column('decimals', sa.SmallInteger(), server_default=sa.text('2'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint("code ~ '^[A-Z]{3}$'", name=op.f('ck_currency_code_format')),
    sa.CheckConstraint('decimals BETWEEN 0 AND 2', name=op.f('ck_currency_decimals_range')),
    sa.ForeignKeyConstraint(['created_by'], ['app_user.id'], name=op.f('fk_currency_created_by_app_user'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['updated_by'], ['app_user.id'], name=op.f('fk_currency_updated_by_app_user'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_currency')),
    sa.UniqueConstraint('code', name=op.f('uq_currency_code'))
    )
    op.create_table('company',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('legal_name', sa.String(length=250), nullable=False),
    sa.Column('tax_number', sa.String(length=11), nullable=False),
    sa.Column('tax_office', sa.String(length=100), nullable=False),
    sa.Column('currency_id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint("tax_number ~ '^[0-9]{10,11}$'", name=op.f('ck_company_tax_number_format')),
    sa.ForeignKeyConstraint(['created_by'], ['app_user.id'], name=op.f('fk_company_created_by_app_user'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['currency_id'], ['currency.id'], name=op.f('fk_company_currency_id_currency'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['updated_by'], ['app_user.id'], name=op.f('fk_company_updated_by_app_user'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_company')),
    sa.UniqueConstraint('name', name=op.f('uq_company_name')),
    sa.UniqueConstraint('tax_number', name=op.f('uq_company_tax_number'))
    )
    op.create_index(op.f('ix_company_currency_id'), 'company', ['currency_id'], unique=False)
    op.create_table('exchange_rate',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('currency_id', sa.BigInteger(), nullable=False),
    sa.Column('rate_date', sa.Date(), nullable=False),
    sa.Column('buying', sa.Numeric(precision=18, scale=6), nullable=False),
    sa.Column('selling', sa.Numeric(precision=18, scale=6), nullable=False),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.CheckConstraint('buying > 0', name=op.f('ck_exchange_rate_buying_positive')),
    sa.CheckConstraint('selling >= buying', name=op.f('ck_exchange_rate_selling_not_below_buying')),
    sa.ForeignKeyConstraint(['created_by'], ['app_user.id'], name=op.f('fk_exchange_rate_created_by_app_user'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['currency_id'], ['currency.id'], name=op.f('fk_exchange_rate_currency_id_currency'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['updated_by'], ['app_user.id'], name=op.f('fk_exchange_rate_updated_by_app_user'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_exchange_rate')),
    sa.UniqueConstraint('currency_id', 'rate_date', name=op.f('uq_exchange_rate_currency_id_rate_date'))
    )
    for table in AUDITED_TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_set_updated_at BEFORE UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
        )


def downgrade() -> None:
    op.drop_table('exchange_rate')
    op.drop_index(op.f('ix_company_currency_id'), table_name='company')
    op.drop_table('company')
    op.drop_table('currency')
    op.drop_index('ix_app_user_email_lower', table_name='app_user')
    op.drop_table('app_user')
