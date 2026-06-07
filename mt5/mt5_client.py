import asyncio
import threading
import queue
import pandas as pd
import socket
import os

# ---------- DNS patch ----------
def _patch_aiohttp_dns():
    try:
        import aiohttp.resolver
        from aiohttp.resolver import AsyncResolver
        import dns.asyncresolver
        original_resolve = AsyncResolver.resolve

        async def patched_resolve(self, host, port=0, family=socket.AF_UNSPEC):
            if 'agiliumtrade.ai' in host:
                resolver = dns.asyncresolver.Resolver()
                resolver.nameservers = ['8.8.8.8', '8.8.4.4']
                try:
                    answers = await resolver.resolve(host, 'A')
                    ip = str(answers[0])
                    return [{'hostname': host, 'host': ip, 'port': port,
                             'family': socket.AF_INET, 'proto': 6, 'flags': 0}]
                except Exception as e:
                    print(f"[DNS patch] resolve failed: {e}")
            return await original_resolve(self, host, port, family)

        AsyncResolver.resolve = patched_resolve
        print("[DNS] aiohttp DNS patch applied")
    except Exception as e:
        print(f"[DNS] patch not applied: {e}")

_patch_aiohttp_dns()

from metaapi_cloud_sdk import MetaApi

class MT5Client:
    def __init__(self, api_token, account_id):
        self.api_token = api_token
        self.account_id = account_id
        self._loop = None
        self._thread = None
        self._ready = threading.Event()
        self.connection = None
        self.account = None
        self._error = None

    def start(self):
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=60):
            raise Exception("Timeout connecting to MetaApi")
        if self._error:
            raise self._error

    def _run_event_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_connect())
        except Exception as e:
            self._error = e
            self._ready.set()
            return
        self._loop.run_forever()

    async def _async_connect(self):
        print(f"[MetaApi] Connecting to account {self.account_id} ...")
        api = MetaApi(self.api_token)
        self.account = await api.metatrader_account_api.get_account(self.account_id)
        if not self.account:
            raise Exception("Account not found – check METAAPI_ACCOUNT_ID in .env")
        # Force region to match where the account is deployed (London worked in WS logs)
        self.connection = self.account.get_rpc_connection()
        await self.connection.connect()
        await self.connection.wait_synchronized()
        print("[MetaApi] Connected successfully.")
        self._ready.set()

    def _run_async(self, coro_func, *args, **kwargs):
        if not self._loop or not self._loop.is_running():
            raise Exception("Event loop not running")
        q = queue.Queue()
        async def wrapper():
            try:
                res = await coro_func(*args, **kwargs)
                q.put(res)
            except Exception as e:
                q.put(e)
        asyncio.run_coroutine_threadsafe(wrapper(), self._loop)
        res = q.get(timeout=60)
        if isinstance(res, Exception):
            raise res
        return res

    def get_account_info(self):
        return self._run_async(self.connection.get_account_information)

    def get_current_price(self, symbol):
        async def _get():
            spec = await self.connection.get_symbol_specification(symbol)
            price = await self.connection.get_symbol_price(symbol)
            return {'bid': price['bid'], 'ask': price['ask'], 'digits': spec['digits']}
        return self._run_async(_get)

    # Historical candles are now provided by data_provider.py – this method is unused
    def get_candles(self, symbol, timeframe, limit=200):
        raise NotImplementedError("Use data_provider.get_candles instead")

    def place_order(self, symbol, order_type, volume, sl=None, tp=None, comment='ITT Bot'):
        async def _place():
            if order_type == 'buy':
                res = await self.connection.create_market_buy_order(
                    symbol, volume, stop_loss=sl, take_profit=tp, comment=comment
                )
            else:
                res = await self.connection.create_market_sell_order(
                    symbol, volume, stop_loss=sl, take_profit=tp, comment=comment
                )
            if res.get('error'):
                raise Exception(res['error'])
            return res['orderId']
        return self._run_async(_place)
