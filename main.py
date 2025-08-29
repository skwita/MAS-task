import asyncio
import logging

from model.Agents.DirectorAgent import DirectorAgent
from model.Agents.ProductionAgent import ProductionAgent
from model.Agents.QualityAgent import QualityAgent
from model.Agents.SalesAgent import SalesAgent
from model.Environment import Environment
from service.MessageBus import MessageBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


async def main():
    env = Environment()
    bus = MessageBus()

    production = ProductionAgent("production", bus, env)
    quality = QualityAgent("quality", bus, env)
    sales = SalesAgent("sales", bus, env)
    director = DirectorAgent("director", bus, env)

    tasks = [
        asyncio.create_task(a.run())
        for a in (production, quality, sales, director)
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())