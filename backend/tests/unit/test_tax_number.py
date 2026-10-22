"""
file: test_tax_number.py

VKN ve TCKN kontrol hanesi fonksiyonlarını bilinen geçerli numaralarla ve
onların bozulmuş halleriyle dener.

description: tax_number modülünün birim testleri.
"""

import pytest

from erp.modules.organization.tax_number import is_valid_tax_number, is_valid_tckn, is_valid_vkn

# 4540536920 python-stdnum'un belgesindeki örnek VKN. 1234567890 bu projede
# deneme şirketi için hesaplandı. 10000000146 yaygın kullanılan bir deneme TCKN'si.
VALID_VKNS = ["4540536920", "1234567890"]
VALID_TCKN = "10000000146"


@pytest.mark.parametrize("number", VALID_VKNS)
def test_valid_vkn(number: str) -> None:
    assert is_valid_vkn(number)
    assert is_valid_tax_number(number)


# Son hane dışındaki dokuz değerin hepsi reddedilmeli, kontrol hanesi tek bir
# değere izin verir.
@pytest.mark.parametrize("number", VALID_VKNS)
def test_vkn_with_wrong_check_digit(number: str) -> None:
    wrong = [number[:9] + d for d in "0123456789" if d != number[9]]
    assert not any(is_valid_vkn(n) for n in wrong)


def test_valid_tckn() -> None:
    assert is_valid_tckn(VALID_TCKN)
    assert is_valid_tax_number(VALID_TCKN)


@pytest.mark.parametrize("number", ["10000000147", "10000000156", "00000000146"])
def test_invalid_tckn(number: str) -> None:
    assert not is_valid_tckn(number)


# Biçimi bozuk girdiler hata fırlatmadan reddedilmeli. Arapça rakamlar
# isdigit'ten geçtiği için ayrıca denenir.
@pytest.mark.parametrize("number", ["", "123", "45405369A0", "4540 53692", "٤٥٤٠٥٣٦٩٢٠", "123456789012"])
def test_malformed_numbers(number: str) -> None:
    assert not is_valid_tax_number(number)
