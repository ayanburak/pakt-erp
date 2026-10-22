/*
file: bootstrap.sql

PostgreSQL üzerinde pakt-erp için rolleri ve veritabanlarını kurar. psql ile,
superuser olarak ve PostgreSQL 16 ya da daha yeni bir sürümde çalıştırılır.
migrator değişkeni zorunludur, migration'ları çalıştıracak ve giriş yapabilen
kullanıcının adıdır. db, owner ve app değişkenleri verilmezse pakt_erp,
pakt_erp_owner ve pakt_erp_app kullanılır. Test veritabanının adı db'nin
sonuna _test eklenerek bulunur.

    sudo -u postgres psql -X -v migrator=burak < sql/bootstrap.sql

Dosya tekrar çalıştırılabilir. Var olan bir rol ya da veritabanı yeniden
kurulmaz, yetkiler yeniden verilir. Uygulama rolünün şifresi burada verilmez,
psql içinde \password komutuyla ayrıca girilir.

description: pakt-erp'nin rollerini, ana ve test veritabanını ve yetkilerini kurar.
*/

-- Üç rol var. owner bütün tabloların sahibidir ama giriş yapamaz, böylece şemayı
-- değiştirebilen kimlik dışarıdan doğrudan ele geçirilemez. app uygulamanın
-- bağlandığı roldür, sadece satır okuyup yazar, tablo kuramaz ve silemez.
-- migrator giriş yapabilen bir kullanıcıdır ve owner'a INHERIT FALSE ile üye
-- yapılır. Yani owner'ın yetkilerini kendiliğinden taşımaz, sadece SET ROLE ile
-- owner'a geçince şema değiştirebilir. Alembic bağlanınca bu geçişi yapar, bu
-- sayede migration'ın kurduğu her nesnenin sahibi owner olur. INHERIT ve SET
-- seçenekleri PostgreSQL 16 ile geldiği için daha eski sürümde dosya çalışmaz.
--
-- NOTE: app'e sequence yetkisi verilmez. Tablolarda id'ler identity sütunuyla
-- üretilecek, identity sütununa INSERT yapmak için tablodaki INSERT yetkisi
-- yeterli. serial kullanılırsa ya da bir yerde nextval doğrudan çağrılırsa
-- buraya sequence yetkisi eklemek gerekir.

\set ON_ERROR_STOP on

-- --- Değişkenler ---

\if :{?db}
\else
    \set db pakt_erp
\endif
\if :{?owner}
\else
    \set owner pakt_erp_owner
\endif
\if :{?app}
\else
    \set app pakt_erp_app
\endif
\set test_db :db _test

-- Kişisel bir kullanıcı adı varsayılan olarak yazılmaz, bu yüzden migrator
-- verilmemişse dosya hiçbir şey kurmadan hata verip durur.
\if :{?migrator}
\else
    DO $$ BEGIN RAISE EXCEPTION 'migrator değişkeni verilmedi. Örnek: psql -v migrator=burak'; END $$;
\endif

-- --- Roller ---

SELECT format('CREATE ROLE %I %s', r.name, r.options)
FROM (VALUES (:'owner', 'NOLOGIN'),
             (:'app', 'LOGIN'),
             (:'migrator', 'LOGIN')) AS r(name, options)
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = r.name)
\gexec

GRANT :"owner" TO :"migrator" WITH INHERIT FALSE, SET TRUE;

-- --- Veritabanları ---

SELECT format('CREATE DATABASE %I OWNER %I', d.name, :'owner')
FROM (VALUES (:'db'), (:'test_db')) AS d(name)
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = d.name)
\gexec

-- --- Yetkiler ---

-- Şema ve varsayılan yetkiler veritabanına özeldir, bu yüzden aynı blok iki
-- veritabanına ayrı ayrı bağlanılarak çalıştırılır. PUBLIC'ten alınan yetki,
-- sunucudaki her rolün bu veritabanına bağlanabilmesini kapatır. ALTER DEFAULT
-- PRIVILEGES ileride owner'ın kuracağı her tabloya app'in yetkisini kendiliğinden
-- verir, böylece her migration'da ayrıca GRANT yazmak gerekmez.

\connect :db
REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db" TO :"app", :"migrator";
GRANT USAGE ON SCHEMA public TO :"app";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app";

\connect :test_db
REVOKE ALL ON DATABASE :"test_db" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"test_db" TO :"app", :"migrator";
GRANT USAGE ON SCHEMA public TO :"app";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app";

\echo 'Kurulum tamamlandı.'
