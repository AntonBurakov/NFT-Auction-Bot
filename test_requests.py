import unittest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, text
from app.database.models import async_session, User, Nft, Lot, async_main
from app.database.requests import set_user, set_nft, get_user_nfts, get_nft, get_user_lots, get_open_lots, place_bid, create_lot

class UserRequestsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await async_main()
        await set_user(123456789)

    async def asyncTearDown(self):
        async with async_session() as session:
            await session.execute(text('DELETE FROM users WHERE tg_id = 123456789'))
            await session.commit()

    async def test_set_user(self):
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.tg_id == 123456789))
            self.assertIsNotNone(user)


class NftRequestsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await async_main()
        await set_user(123456789)
        await set_nft("http://example.com/nft1", 123456789)

        async with async_session() as session:
            await session.execute(
                text("INSERT INTO nfts (href, user_id) VALUES ('http://example.com/nft2', 123456789)")
            )
            await session.execute(
                text("INSERT INTO nfts (href, user_id) VALUES ('http://example.com/nft3', 123456789)")
            )
            await session.commit()

    async def asyncTearDown(self):
        async with async_session() as session:
            await session.execute(text('DELETE FROM nfts WHERE user_id = 123456789'))
            await session.execute(text('DELETE FROM users WHERE tg_id = 123456789'))
            await session.commit()

    async def test_set_nft(self):
        async with async_session() as session:
            nfts = await session.scalar(select(Nft).where(Nft.href == "http://example.com/nft1"))
            self.assertIsNotNone(nfts)

    async def test_get_nfts(self):
        nfts = await get_user_nfts(123456789)
        self.assertEqual(nfts, ["http://example.com/nft1", "http://example.com/nft2", "http://example.com/nft3"])

    async def test_get_nft(self):
        async with async_session() as session:
            nft = await session.scalar(select(Nft).where(Nft.href == "http://example.com/nft3"))
            self.assertIsNotNone(nft)


class LotRequestsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await async_main()
        await set_user(123456789)
        await set_user(987654321)
        await set_nft("http://example.com/nft1", 123456789)
        await create_lot(1, 123456789, 100)

        async with async_session() as session:
            await session.execute(
                text("INSERT INTO lots (nft_id, user_id, starting_price, end_time, is_active) VALUES ('1', 123456789, 110, '2024-10-30 21:34:33.831577', True)")
            )
            await session.commit()

    async def asyncTearDown(self):
        async with async_session() as session:
            await session.execute(text('DELETE FROM lots WHERE user_id = 123456789'))
            await session.execute(text('DELETE FROM nfts WHERE user_id = 123456789'))
            await session.execute(text('DELETE FROM users WHERE tg_id = 123456789'))
            await session.commit()

    async def test_create_lot(self):
        async with async_session() as session:
            lots = await session.scalar(select(Lot).where(Lot.user_id == 123456789))
            self.assertIsNotNone(lots)

    async def test_get_user_lots(self):
        lots = await get_user_lots(123456789)
        self.assertEqual(len(lots), 2)
        starting_prices = [lot.starting_price for lot in lots]
        expected_prices = [100, 110]  
        self.assertCountEqual(starting_prices, expected_prices)


    async def test_get_open_lots(self):
        lots = await get_open_lots(987654321)
        self.assertEqual(len(lots), 2)
        starting_prices = [lot.starting_price for lot in lots]
        expected_prices = [100, 110]  
        self.assertCountEqual(starting_prices, expected_prices)


    async def test_place_bid(self):
        await place_bid(1, 987654321, 150)
        async with async_session() as session:
            lot = await session.scalar(select(Lot).where(Lot.id == 1))
            self.assertEqual(lot.current_bid, 150)
            self.assertEqual(lot.highest_bidder_id, 987654321)


if __name__ == "__main__":
    unittest.main()
