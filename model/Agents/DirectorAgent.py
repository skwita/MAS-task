import asyncio
from typing import List, Tuple
from model.Agents.Agent import Agent
from model.data.Plan import Plan
from model.data.PlanMetrics import PlanMetrics
from util.Util import as_table, dict_to_metrics, dict_to_plan


class DirectorAgent(Agent):
    async def run(self):
        # Запрос KPI у нижнего уровня (они не могут отказать)
        for target in ("production", "quality", "sales"):
            await self.send(target, "kpi_request", {"need": "metrics"})

        reports: List[Tuple[str, Plan, PlanMetrics]] = []

        # Ждем отчеты от всех
        deadline = asyncio.get_event_loop().time() + 2.0
        while asyncio.get_event_loop().time() < deadline:
            msg = await self.recv(timeout=0.2)
            if not msg:
                continue
            if msg.topic == "report":
                p = dict_to_plan(msg.payload["plan"])
                m = dict_to_metrics(msg.payload["metrics"])
                reports.append((msg.sender, p, m))
            elif msg.topic == "kpi_response":
                p = dict_to_plan(msg.payload["plan"])
                m = dict_to_metrics(msg.payload["metrics"])
                reports.append((msg.payload.get("agent", msg.sender), p, m))

        # Если кто-то не отчитался — все равно принимаем решение по имеющимся
        if not reports:
            # резервный вариант — базовый план
            base = Plan(2, 0, False, False)
            decision = base, self.env.evaluate(base)
        else:
            # Сравнение планов по выручке среди выполнимых
            feasible_reports = [(a, p, m) for (a, p, m) in reports if m.feasible]
            candidates = feasible_reports or reports
            decision_agent, decision_plan, decision_metrics = max(candidates, key=lambda t: t[2].revenue)
            decision = decision_plan, decision_metrics

        # Публикуем итог
        plan, metrics = decision
        await self.send("all", "final_decision", {
            "plan": plan.to_dict(),
            "metrics": metrics.__dict__,
        })
        # Для визуального вывода в консоль
        print("\n===== ИТОГОВЫЙ ПЛАН (директор) =====")
        print(as_table(plan, metrics))