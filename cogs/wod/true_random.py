import os
from uuid import uuid4
from aiohttp import ClientSession

RANDOMORG_URL = 'https://api.random.org/json-rpc/4/invoke'


class D10Pool:
    def __init__(self):
        self.session: ClientSession = ClientSession()
        self.pool: list[int] = []

    async def next(self) -> int:
        if not self.pool:
            await self.update_pool()
        return self.pool.pop()

    async def update_pool(self) -> None:
        params = {
            'jsonrpc': '2.0',
            'method': 'generateIntegers',
            'params': {
                'apiKey': os.getenv('RANDOMORG_KEY'),
                'n': 75,
                'min': 1,
                'max': 10
            },
            'id': uuid4().hex
        }
        async with self.session.post(RANDOMORG_URL, json=params) as response:
            data = await response.json()
            self.pool = data['result']['random']['data']
