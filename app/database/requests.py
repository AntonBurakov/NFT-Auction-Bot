from app.database.models import async_session
from app.database.models import User, Nft
from sqlalchemy import select


async def set_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()


async def set_nft(href: str, tg_id: int):
    async with async_session() as session:
        session.add(Nft(href=href, user_id=tg_id))
        await session.commit()

async def get_user_nfts(tg_id: int):
    async with async_session() as session:
        # Получаем пользователя по tg_id
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            # Получаем все Nft, связанные с данным пользователем
            result = await session.execute(select(Nft.href).where(Nft.user_id == user.tg_id))
            nfts = result.scalars().all()
            return nfts
        else:
            return []  # Возвращаем пустой список, если пользователь не найден