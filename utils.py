from typing import Awaitable, TypeVar
import asyncio
import sys

T = TypeVar('T')

async def put_waiting(message:str, waitable:Awaitable[T]) -> T:
	async def warper() -> T:
		return await waitable 
	task = asyncio.create_task(warper())
	sys.stdout.write(f'\r{message}  ')
	try:
		while not task.done():
			for symbol in ['|', '/', '-', '\\']:
				sys.stdout.write(f'\b{symbol}')
				sys.stdout.flush()
				await asyncio.sleep(0.1)
		sys.stdout.write(f'\bOK\n')
		sys.stdout.flush()
	except asyncio.CancelledError:
		task.cancel()
	return await task
