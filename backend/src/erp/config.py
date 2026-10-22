"""
file: config.py
importable: Settings

Settings uygulamanın ayarlarını ortam değişkenlerinden ve backend klasöründeki
.env dosyasından okur. Aynı isimde bir ortam değişkeni varsa .env'deki değerin
önüne geçer. Zorunlu bir ayar eksikse Settings() ValidationError fırlatır.
Bağlantı adresleri şifre taşıdığı için SecretStr olarak tutulur, açık hali
get_secret_value() ile alınır.

description: Uygulamanın ortamdan ve .env dosyasından okunan ayarlarını tanımlar.
"""

# NOTE: .env'in yeri çalışılan klasöre göre değil bu dosyanın yerine göre
# bulunur, böylece alembic ya da pytest hangi klasörden çalıştırılırsa
# çalıştırılsın aynı dosya okunur. Bu yol paketin src altından, uv'nin
# kurduğu düzenlenebilir haliyle çalıştığını varsayar. Paket başka bir yere
# kopyalanarak kurulursa .env bulunamaz ve ayarlar sadece ortam
# değişkenlerinden gelir.

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


# migration_role boş bırakılabilir. Boşsa migration'lar bağlanan kullanıcının
# kendi kimliğiyle çalışır, doluysa env.py bağlanır bağlanmaz bu role geçer.
class Settings(BaseSettings):
    """Uygulamanın ayarları.

    Args:
        database_url: Uygulamanın bağlandığı, sadece satır okuyup yazabilen rolün adresi.
        migration_database_url: Migration'ları çalıştıran kullanıcının adresi.
        migration_role: Migration'dan önce geçilecek, tabloların sahibi olan rol.
    """

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: SecretStr
    migration_database_url: SecretStr
    migration_role: str = ""
