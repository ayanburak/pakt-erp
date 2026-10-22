"""
file: dependencies.py
importable: get_session, SessionDep

Uç noktaların ortak bağımlılıkları. SessionDep alan bir uç nokta, o isteğe
özel bir veritabanı oturumu alır. Oturumun transaction'ı uç nokta hatasız
biterse commit edilir, bir hata çıkarsa geri alınır.

description: Her HTTP isteğine kendi veritabanı oturumunu ve transaction'ını veren bağımlılık.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


# Oturum üreticisi uygulama açılırken main.py'de app.state'e konur. Uç nokta
# bir hata fırlatırsa FastAPI bu hatayı yield satırına geri iletir,
# session.begin() bloğu da hatayı görünce transaction'ı geri alır.
async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session, session.begin():
        yield session


# scope="function" commit'in cevap istemciye gönderilmeden önce yapılmasını
# sağlar. Varsayılan davranışta commit cevaptan sonra çalışırdı ve commit
# başarısız olsa bile istemci başarılı cevabı almış olurdu.
SessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]
