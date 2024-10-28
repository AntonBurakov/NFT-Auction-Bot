from app.database.models import async_session
from app.database.models import User, Nft, Lot
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
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            result = await session.execute(select(Nft.href).where(Nft.user_id == user.tg_id))
            nfts = result.scalars().all()
            return nfts
        else:
            return []  

async def get_nft(nft_id: int):
    async with async_session() as session:
        result = await session.execute(select(Nft).where(Nft.id == nft_id))
        nft = result.scalars().first()  
        return nft


async def create_lot(nft_id: int, user_id: int, starting_price: int):
    async with async_session() as session:
        session.add(Lot(nft_id=nft_id, user_id=user_id, starting_price=starting_price, current_bid=None))
        await session.commit()


async def get_user_lots(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Lot).where(Lot.user_id == user_id, Lot.is_active == True))
        return result.scalars().all()


async def get_open_lots(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Lot).where(Lot.user_id != user_id, Lot.is_active == True))
        return result.scalars().all()


async def place_bid(lot_id: int, bidder_id: int, bid_amount: int):
    async with async_session() as session:
        lot = await session.scalar(select(Lot).where(Lot.id == lot_id, Lot.is_active == True))
        if lot and (lot.current_bid is None or bid_amount > lot.current_bid) and bid_amount > lot.starting_price:
            lot.current_bid = bid_amount
            lot.highest_bidder_id = bidder_id
            await session.commit()