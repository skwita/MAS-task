import asyncio
from typing import Dict, Optional
from model.data.Message import Message

class MessageBus:
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue[Message]] = {}

    def register(self, agent_name: str):
        self.queues[agent_name] = asyncio.Queue()

    async def send(self, msg: Message):
        if msg.receiver in self.queues:
            await self.queues[msg.receiver].put(msg)

    async def recv(self, agent_name: str, timeout: float = 5.0) -> Optional[Message]:
        try:
            return await asyncio.wait_for(self.queues[agent_name].get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
