"""
file: models.py

Bütün modüllerin tablolarını Base.metadata'ya kaydeder. Bu dosya import
edildiğinde her modülün models.py dosyası import edilmiş olur. Uygulama
main.py'den, Alembic env.py'den bu dosyayı import eder.

description: Bütün modüllerin tablo tanımlarını tek yerden kaydeden liste.
"""

# XXX: Yeni bir modül tablo kazandığında models.py dosyası buraya eklenmeli.
# Eksik kalan bir modülün tabloları Base.metadata'ya girmez. O zaman
# autogenerate o tabloları görmez, hatta silmeyi önerebilir. O tabloyu
# yabancı anahtarla gösteren bir kayıt da yazılırken NoReferencedTableError
# verir. tests/unit/test_model_registry.py ikinci durumu yakalar.

import erp.modules.currency.models  # noqa: F401
import erp.modules.identity.models  # noqa: F401
import erp.modules.organization.models  # noqa: F401
