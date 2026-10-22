"""
file: errors.py
importable: CompanyNotFound, CompanyNameTaken, TaxNumberTaken, UnknownCurrency, InvalidTaxNumber

organization modülünün iş hataları. Her biri erp.shared.errors'taki bir
türden türer, web katmanı HTTP kodunu bu türe bakarak seçer.

description: organization modülünün iş hatalarını tanımlar.
"""

from erp.shared.errors import Conflict, InvalidInput, NotFound


class CompanyNotFound(NotFound):
    message = "Şirket bulunamadı."


class CompanyNameTaken(Conflict):
    message = "Bu adla kayıtlı bir şirket var."


class TaxNumberTaken(Conflict):
    message = "Bu vergi numarasıyla kayıtlı bir şirket var."


class UnknownCurrency(InvalidInput):
    message = "Para birimi bulunamadı."


class InvalidTaxNumber(InvalidInput):
    message = "Vergi numarası geçersiz."
