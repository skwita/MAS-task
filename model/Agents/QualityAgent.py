from typing import List
from model.Agents.Agent import Agent
from model.data.Plan import Plan
from util.Util import dict_to_plan


class QualityAgent(Agent):
    def better_quality_variants(self, base_plan: Plan) -> List[Plan]:
        # Перебираем только качество, остальное из базового плана
        opts = []
        for bm, bs in [(False, False), (True, False), (False, True), (True, True)]:
            opts.append(Plan(base_plan.batches, base_plan.replace_equip, bm, bs))
        return opts

    def score(self, plan: Plan) -> float:
        m = self.env.evaluate(plan)
        # минимизируем дефект, штраф за выход за бюджет
        return -(m.defective_units) - 1000 * (0 if m.feasible else 1)

    async def run(self):
        # ждем план на проверку
        base = await self.recv(timeout=2.0)
        if base and base.topic == "check":
            plan = dict_to_plan(base.payload["plan"])
            variants = self.better_quality_variants(plan)
            best_for_quality = max(variants, key=self.score)
            # Если мы можем улучшить дефект без выхода за бюджет — предлагаем встречный
            if self.env.evaluate(best_for_quality).defective_units < self.env.evaluate(plan).defective_units:
                await self.send("production", "counter_proposal", {"plan": best_for_quality.to_dict()})
        # По запросу директора — отчитываемся
        # (директор будет рассылать отдельные запросы)
        # Цикл прослушивания
        while True:
            msg = await self.recv(timeout=0.5)
            if not msg:
                break
            if msg.topic == "kpi_request":
                # отчитаем локальные KPI по лучшему варианту относительно последнего известного плана производства
                last_plan = plan if base else Plan(2, 0, False, False) # type: ignore
                best = max(self.better_quality_variants(last_plan), key=self.score)
                await self.send("director", "kpi_response", {"agent": self.name, "plan": best.to_dict(), "metrics": self.env.evaluate(best).__dict__})
