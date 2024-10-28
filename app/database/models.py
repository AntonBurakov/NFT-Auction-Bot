from sqlalchemy import BigInteger, String, ForeignKey, DateTime, Integer, Boolean 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime, timedelta

engine = create_async_engine(url='sqlite+aiosqlite:///app_data/db.sqlite3')

async_session = async_sessionmaker(engine)



class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)


class Nft(Base):
    __tablename__ = 'nfts'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    href: Mapped[str] = mapped_column(String(40))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'))

class Lot(Base):
    __tablename__ = 'lots'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nft_id: Mapped[int] = mapped_column(ForeignKey('nfts.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'))
    starting_price: Mapped[int] = mapped_column(Integer)
    current_bid: Mapped[int] = mapped_column(Integer, nullable=True)
    highest_bidder_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'), nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    is_active: Mapped[bool] = mapped_column(default=True)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)