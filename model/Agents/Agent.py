import logging
from typing import Any, Dict, Optional

from model.Environment import Environment
from model.data.Message import Message
from model.data.Plan import Plan
from service.MessageBus import MessageBus

class Agent:
    def __init__(self, name: str, msg_bus: MessageBus, env: Environment):
        self.name = name
        self.msg_bus = msg_bus
        self.env = env
        self.msg_bus.register(self.name)
        self.local_memory: Dict[str, Any] = {}
        self.log = logging.getLogger(self.name)
    
    async def send(self, to: str, topic: str, payload: Dict[str, Any]):
        self.log.info(f"Отправка сообщения -> {to}, тема={topic}, данные={payload}")
        await self.msg_bus.send(Message(self.name, to, topic, payload))

    async def recv(self, timeout: float = 5.0) -> Optional[Message]:
        msg = await self.msg_bus.recv(self.name, timeout)
        if msg:
            self.log.info(f"Получено сообщение <- {msg.sender}, тема={msg.topic}, данные={msg.payload}")
        return msg
    
    def score(self, plan: Plan) -> float:
        raise NotImplementedError        

    async def run(self):
        raise NotImplementedError