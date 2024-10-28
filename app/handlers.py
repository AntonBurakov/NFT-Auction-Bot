from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import requests
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
from dotenv import load_dotenv
import app.database.requests as rq

router = Router()
load_dotenv()

opensea_token = os.getenv('OPENSEA_API_KEY')

class NFTAccount(StatesGroup):
    account = State()
    blockchain = State()


class LotCreation(StatesGroup):
    choose_nft_for_lot = State()  
    set_starting_price = State()  


class BidCreation(StatesGroup):
    lot_number = State()  
    bid_amount = State() 

class NFT(StatesGroup):
    address = State()
    chain = State()
    identifier = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer('Привет!\nЯ бот-аукционер. С помощью меня ты можешь найти лучшего покупателя для своих NFT или же поучаствовать в торгах.\nДля продавцов:\n1. /sync_nfts - Загрузка твоих NFT с nft маркета OpenSea.🔄\n2. /list_nfts_for_lot - Просмотр твоей коллекции NFT. Здесь же ты можешь выставить лот. 🏞️ \n3. /list_my_lots - Просмотр лотов выставленных мною. 📝 \n\nДля покупателей:\n1. /list_open_lots - просмотр открытых лотов.👀\n2. /get_nft - поиск nft на nft маркете')


@router.message(Command('sync_nfts'))
async def nft_synchronization(message: Message, state: FSMContext):
    await state.set_state(NFTAccount.account)
    await message.answer('Введите свой публичный блокчейн-адрес.')


@router.message(NFTAccount.account)
async def register_account(message: Message, state: FSMContext):
    await state.update_data(account=message.text)
    await state.set_state(NFTAccount.blockchain)
    await message.answer('Введите название блокчейн сети.')

@router.message(NFTAccount.blockchain)
async def register_blockchain(message: Message, state: FSMContext):
    await state.update_data(blockchain=message.text)

    user_data = await state.get_data()
    blockchain = user_data.get('blockchain')
    account = user_data.get('account')

    url = f"https://api.opensea.io/api/v2/chain/{blockchain}/account/{account}/nfts"

    headers = {
        'x-api-key': opensea_token  
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        nfts = data.get('nfts', [])
        for nft in nfts:
            image_url = nft.get('image_url')
            if image_url:
                await rq.set_nft(href=image_url, tg_id=message.from_user.id)
    else:
        await message.answer(f"Ошибка: {response.status_code} {response.reason}")
    
    await state.clear()


@router.message(Command('list_nfts_for_lot'))
async def list_nfts_for_lot(message: Message):
    tg_id = message.from_user.id
    nfts = await rq.get_user_nfts(tg_id)

    if not nfts:
        await message.answer("У вас нет NFT для выставления на лот.")
        return

    for href in nfts:
        await message.answer_photo(href) 

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Да", callback_data="create_lot_yes")
    keyboard.button(text="Нет", callback_data="create_lot_no")
    await message.answer("Хотите выставить лот?", reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "create_lot_yes")
async def ask_nft_for_lot(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите номер NFT, который хотите выставить на лот:")
    await state.set_state(LotCreation.choose_nft_for_lot)

@router.callback_query(F.data == "create_lot_no")
async def cancel_lot_creation(call: CallbackQuery):
    await call.message.answer("Лот не будет создан.")
    await call.answer() 


@router.message(LotCreation.choose_nft_for_lot)
async def ask_starting_price(message: Message, state: FSMContext):
    await state.update_data(choose_nft_for_lot=int(message.text))
    nft_number = int(message.text)
    # Получаем данные о NFT
    user_data = await state.get_data()
    tg_id = message.from_user.id
    nfts = await rq.get_user_nfts(tg_id)

    if nft_number < 0 or nft_number >= len(nfts):
        await message.answer("Неверный номер NFT. Попробуйте снова.")
        return

    selected_nft = nfts[nft_number]
    await message.answer("Введите начальную цену")
    await state.set_state(LotCreation.set_starting_price)

@router.message(LotCreation.set_starting_price)
async def create_lot(message: Message, state: FSMContext):
    lot_data = await state.get_data()
    nft_number = lot_data.get('choose_nft_for_lot')
    try:
        starting_price = int(message.text) 
    except ValueError:
        await message.answer("Неверная стоимость. Введите число.")
        return

    user_data = await state.get_data()
    await rq.create_lot(nft_id=nft_number, user_id=message.from_user.id, starting_price=starting_price)

    await message.answer(f"Лот создан с начальной стоимостью {starting_price}.")
    await state.clear()




@router.message(Command('list_my_lots'))
async def list_my_lots(message: Message):
    tg_id = message.from_user.id
    lots = await rq.get_user_lots(tg_id)

    if not lots:
        await message.answer("У вас нет активных лотов.")
        return

    for lot in lots:
        await message.answer(f"Лот ID: {lot.id}\nНачальная цена: {lot.starting_price}\nТекущая ставка: {lot.current_bid or 'Нет'}\nПользователь: {lot.highest_bidder_id or 'Нет'}")
        nft = await rq.get_nft(lot.nft_id)
        await message.answer_photo(nft.href)




@router.message(Command('list_open_lots'))
async def list_open_lots(message: Message):
    tg_id = message.from_user.id
    open_lots = await rq.get_open_lots(tg_id)

    if not open_lots:
        await message.answer("Нет доступных лотов.")
        return

    for lot in open_lots:
        await message.answer(f"Лот ID: {lot.id}\nНачальная цена: {lot.starting_price}\nТекущая ставка: {lot.current_bid or 'Нет'}")
        nft = await rq.get_nft(lot.nft_id)
        await message.answer_photo(nft.href)
        
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Да", callback_data="create_bid_yes")
    keyboard.button(text="Нет", callback_data="create_bid_no")
    await message.answer("Хотите сделать ставку лот?", reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "create_bid_yes")
async def ask_nft_for_lot(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите номер открытого лота:")
    await state.set_state(BidCreation.lot_number)

@router.callback_query(F.data == "create_bid_no")
async def cancel_lot_creation(call: CallbackQuery):
    await call.message.answer("Ставка не будет создана.")
    await call.answer() 

@router.message(BidCreation.lot_number)
async def ask_starting_price(message: Message, state: FSMContext):
    await state.update_data(lot_number=int(message.text))
    await message.answer("Введите ставку")
    await state.set_state(BidCreation.bid_amount)

@router.message(BidCreation.bid_amount)
async def create_lot(message: Message, state: FSMContext):
    await state.update_data(bid_amount=int(message.text))
    lot_data = await state.get_data()
    

    await rq.place_bid(lot_id=lot_data.get('lot_number'), bidder_id=message.from_user.id, bid_amount=lot_data.get('bid_amount'))
    await message.answer("Ваша ставка принята.")
    await state.clear()




@router.message(Command('get_nft'))
async def nft_synchronization(message: Message, state: FSMContext):
    await state.set_state(NFT.address)
    await message.answer('Введите адрес NFT.')


@router.message(NFT.address)
async def register_account(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(NFT.chain)
    await message.answer('Введите название блокчейн сети.')


@router.message(NFT.chain)
async def register_account(message: Message, state: FSMContext):
    await state.update_data(chain=message.text)
    await state.set_state(NFT.identifier)
    await message.answer('Введите id NFT.')

@router.message(NFT.identifier)
async def register_blockchain(message: Message, state: FSMContext):
    await state.update_data(identifier=message.text)

    nft_data = await state.get_data()
    address = nft_data.get('address')
    chain = nft_data.get('chain')
    identifier = nft_data.get('identifier')

    url = f"https://api.opensea.io/api/v2/chain/{chain}/contract/{address}/nfts/{identifier}"

    headers = {
        'x-api-key': opensea_token  
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        nft = data.get('nft', {})
        image_url = nft.get('image_url')
        await message.answer(image_url)
    else:
        await message.answer(f"Ошибка: {response.status_code} {response.reason}")
    
    await state.clear()