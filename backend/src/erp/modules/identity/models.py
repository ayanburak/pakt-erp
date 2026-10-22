"""
file: models.py
importable: AppUser

Sisteme giriş yapan kullanıcıların tablosu. E-posta giriş adıdır ve büyük
küçük harf farkı gözetilmeden benzersizdir. Kullanıcı silinmez, is_active
false yapılarak kapatılır, çünkü oluşturduğu kayıtlar ona bağlıdır.

description: identity modülünün veritabanı tablolarını tanımlar.
"""

# TODO: Kullanıcının hangi şirketlere erişebildiği henüz yok, yetki konusu
# konuşulunca eklenecek. password_hash'i üretecek kütüphane de giriş sistemiyle
# birlikte seçilecek.

from sqlalchemy import CheckConstraint, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from erp.infrastructure.database import AuditMixin, Base


# E-posta girildiği gibi saklanır, benzersizlik lower(email) üzerindeki
# index'le sağlanır. Böylece Ali@x.com ile ali@x.com aynı sayılır ama
# kullanıcının yazdığı biçim kaybolmaz. Format kısıtı sadece tek bir @ ve iki
# yanında boşluksuz bir metin arar, ayrıntılı denetim uygulama katmanında.
class AppUser(AuditMixin, Base):
    __tablename__ = "app_user"
    __table_args__ = (
        CheckConstraint(r"email ~ '^[^@\s]+@[^@\s]+$'", name="email_format"),
        Index("ix_app_user_email_lower", func.lower(text("email")), unique=True),
    )

    email: Mapped[str] = mapped_column(String(254))
    full_name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
