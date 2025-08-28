from model.Agents.Agent import Agent
from model.data.Plan import Plan
from util.Util import dict_to_plan


class SalesAgent(Agent):
    def score(self, plan: Plan) -> float:
        m = self.env.evaluate(plan)
        return m.saleable_units  # максимизируем реализуемые единицы

    async def run(self):
        base = await self.recv(timeout=2.0)
        if base and base.topic == "check":
            plan = dict_to_plan(base.payload["plan"])
            # попробуем увеличить партии до гарантированного спроса, если не нарушаем бюджет
            candidates = []
            for b in [plan.batches, min(4, plan.batches + 1)]:
                candidates.append(Plan(b, plan.replace_equip, plan.better_materials, plan.better_staff))
            best = max(candidates, key=self.score)
            if self.score(best) > self.score(plan):
                await self.send("production", "counter_proposal", {"plan": best.to_dict()})
        # KPI для директора по запросу
        while True:
            msg = await self.recv(timeout=0.5)
            if not msg:
                break
            if msg.topic == "kpi_request":
                last_plan = plan if base else Plan(2, 0, False, False) # type: ignore
                best = max([last_plan, Plan(min(4, last_plan.batches + 1), last_plan.replace_equip, last_plan.better_materials, last_plan.better_staff)], key=self.score)
                await self.send("director", "kpi_response", {"agent": self.name, "plan": best.to_dict(), "metrics": self.env.evaluate(best).__dict__})
