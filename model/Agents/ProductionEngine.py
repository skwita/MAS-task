from typing import List
from model.Agents.Agent import Agent
from model.data.Plan import Plan
from model.config import BUDGET
from util.Util import dict_to_plan


class ProductionAgent(Agent):
    def plan_candidates(self) -> List[Plan]:
        cands: List[Plan] = []
        for batches in [2, 3, 4]:
            for replace in [0, 2, 4, 6]:
                for bm, bs in [(False, False), (True, False), (False, True), (True, True)]:
                    cands.append(Plan(batches=batches, replace_equip=replace,
                                      better_materials=bm, better_staff=bs))
        return cands

    def score(self, plan: Plan) -> float:
        m = self.env.evaluate(plan)
        return m.produced_units - 0.0001 * max(0, m.total_cost - BUDGET)

    async def run(self):
        # 1) Локальное планирование
        cands = self.plan_candidates()
        best = max(cands, key=self.score)
        self.local_memory["best_plan"] = best
        # 2) Broadcast плана для проверки
        await self.send("quality", "check", {"plan": best.to_dict()})
        await self.send("sales", "check", {"plan": best.to_dict()})
        # 3) Ждем замечания и идем на попарные переговоры
        for _ in range(2):
            msg = await self.recv(timeout=1.0)
            if not msg:
                break
            if msg.topic == "counter_proposal":
                # применим простой оператор: если встречная лучше для нас, примем
                counter = dict_to_plan(msg.payload["plan"])
                if self.score(counter) >= self.score(best):
                    best = counter
        # 4) Отправка директору
        await self.send("director", "report", {"plan": best.to_dict(), "metrics": self.env.evaluate(best).__dict__})