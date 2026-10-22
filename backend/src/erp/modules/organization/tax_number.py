"""
file: tax_number.py
importable: is_valid_tax_number, is_valid_vkn, is_valid_tckn

Vergi numarasının son hanesi önceki hanelerden hesaplanan bir kontrol
hanesidir. Bu fonksiyonlar yanlış yazılmış bir numarayı yakalar, ama
numaranın gerçekten birine verilmiş olduğunu göstermez. Girdi sadece
rakamlardan oluşmuyorsa ya da uzunluğu yanlışsa False döner, hata fırlatmaz.

description: VKN ve TCKN'nin kontrol hanelerini doğrulayan saf fonksiyonlar.
"""

# NOTE: VKN algoritması python-stdnum kütüphanesinin stdnum.tr.vkn modülüyle
# karşılaştırılarak doğrulandı, koddan bir şey alınmadı. O kütüphanenin
# belgesinde geçen 4540536920 testlerde geçerli örnek olarak kullanılıyor.


def is_valid_tax_number(number: str) -> bool:
    """Numarayı uzunluğuna göre VKN ya da TCKN olarak doğrular.

    Args:
        number: On haneli VKN ya da on bir haneli TCKN.

    Returns:
        Kontrol haneleri doğruysa True.
    """
    if len(number) == 10:
        return is_valid_vkn(number)
    if len(number) == 11:
        return is_valid_tckn(number)
    return False


# İlk dokuz hanenin her biri soldan sıra numarasına göre kaydırılır, ikinin
# bir kuvvetiyle çarpılıp dokuza göre modu alınır. Burada dikkat edilecek
# nokta şu: kaydırılmış hane sıfır değilken mod sıfır çıkarsa sonuç dokuz
# sayılır. Toplamı ona tamamlayan sayının son hanesi kontrol hanesidir.
def is_valid_vkn(number: str) -> bool:
    """On haneli vergi kimlik numarasının kontrol hanesini doğrular.

    Args:
        number: Doğrulanacak numara.

    Returns:
        Numara on rakamdan oluşuyor ve kontrol hanesi doğruysa True.
    """
    if len(number) != 10 or not number.isascii() or not number.isdigit():
        return False
    total = 0
    for position, digit in enumerate(number[:9]):
        shifted = (int(digit) + 9 - position) % 10
        if shifted == 0:
            continue
        total += (shifted * 2 ** (9 - position)) % 9 or 9
    return (10 - total % 10) % 10 == int(number[9])


# Onuncu hane, tek sıradaki ilk beş hanenin toplamının yedi katından çift
# sıradaki ilk dört hanenin toplamı çıkarılarak bulunur. On birinci hane ilk
# on hanenin toplamının son hanesidir. TCKN sıfırla başlayamaz.
def is_valid_tckn(number: str) -> bool:
    """On bir haneli T.C. kimlik numarasının kontrol hanelerini doğrular.

    Args:
        number: Doğrulanacak numara.

    Returns:
        Numara on bir rakamdan oluşuyor, sıfırla başlamıyor ve iki kontrol hanesi doğruysa True.
    """
    if len(number) != 11 or not number.isascii() or not number.isdigit() or number[0] == "0":
        return False
    digits = [int(d) for d in number]
    odd = sum(digits[0:9:2])
    even = sum(digits[1:8:2])
    return (odd * 7 - even) % 10 == digits[9] and sum(digits[:10]) % 10 == digits[10]
