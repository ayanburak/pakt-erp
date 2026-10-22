"""
file: errors.py
importable: DomainError, NotFound, Conflict, InvalidInput

Modüllerin iş hataları buradaki üç türden birinden türetilir. Tür, hatanın
dışarıya nasıl bildirileceğini belirler, mesaj ise kullanıcıya gösterilecek
Türkçe metindir. Bir alt sınıf mesajını sınıf seviyesinde message olarak
tanımlar, gerekirse örnek oluşturulurken başka bir mesaj verilebilir.

description: Bütün modüllerin iş hatalarının ortak taban sınıflarını tanımlar.
"""


# Servisler HTTP'yi bilmez, sadece bu türleri fırlatır. Hangi türün hangi HTTP
# koduna karşılık geldiğine web katmanı karar verir. Böylece yeni bir modül
# kendi hatasını eklerken web katmanına dokunmak zorunda kalmaz.
class DomainError(Exception):
    """Bütün iş hatalarının tabanı.

    Args:
        message: Varsayılan mesajın yerine gösterilecek Türkçe metin.
    """

    message = "İşlem yapılamadı."

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class NotFound(DomainError):
    """İstenen kayıt yok."""

    message = "Kayıt bulunamadı."


class Conflict(DomainError):
    """İşlem var olan bir kayıtla çakışıyor, örneğin aynı vergi numarası."""

    message = "Bu kayıt zaten var."


class InvalidInput(DomainError):
    """Girdi biçim olarak doğru ama bir iş kuralına uymuyor."""

    message = "Girilen bilgi geçersiz."
