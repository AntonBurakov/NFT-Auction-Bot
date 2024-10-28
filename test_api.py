import unittest
from unittest import mock
from unittest.mock import AsyncMock
import httpx

# Так как реальный поход в базу защит в обработчике, то решил создать аналог этой функции здесь для упрощения процесса тестирования

async def fetch_data(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = await response.json()
            return data.get('nfts', []) 
        else:
            raise ValueError(f'Error: {response.status_code}')

class TestFetchData(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        blockchain = "base"
        account = "wkvnpknmrvkmerwmrvmr"
        self.url = f"https://api.opensea.io/api/v2/chain/{blockchain}/account/{account}/nfts"

    @mock.patch('httpx.AsyncClient.get')
    async def test_fetch_data_success(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={'nfts': ['nft1', 'nft2']}) 
        mock_get.return_value = mock_response

        result = await fetch_data(self.url)

        self.assertEqual(result, ['nft1', 'nft2']) 
        mock_get.assert_called_once_with(self.url)

    @mock.patch('httpx.AsyncClient.get')
    async def test_fetch_data_failure(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as context:
            await fetch_data(self.url)

        self.assertEqual(str(context.exception), 'Error: 404')
        mock_get.assert_called_once_with(self.url)

if __name__ == '__main__':
    unittest.main()
