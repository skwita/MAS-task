import asyncio
from typing import List, Tuple
from model.Agents.Agent import Agent
from model.data.Plan import Plan
from model.data.PlanMetrics import PlanMetrics
from util.Util import dict_to_metrics, dict_to_plan, as_table
from model.config import MAX_NEGOTIATION_ROUNDS, MAX_GLOBAL_ROUNDS


class DirectorAgent(Agent):
    """
    Директор проводит глобальные раунды:
    1) Рассылает стартовый план агентам (decision_round).
    2) Запускает итерации переговоров (negotiate_step) и ждёт "step_done" от всех.
       Если в итерации никто не изменил план -> останавливает переговоры.
    3) Запрашивает KPI (kpi_request) и выбирает лучший по выручке.
    4) Раздаёт выбранный план всем (adopt_plan) и начинает следующий глобальный раунд
       от этого плана. Если следующий раунд сразу стабилен, завершает работу и печатает итог.
    """
    async def run(self):
        current_global_plan = Plan(2, 0, False, False)

        for round_idx in range(MAX_GLOBAL_ROUNDS):
            # 1) Разослать базовый план раунда
            for target in ("production", "quality", "sales"):
                await self.send(target, "decision_round", {"plan": current_global_plan.to_dict()})

            # 2) Итерации переговоров нижнего уровня
            stabilized = False
            for it in range(MAX_NEGOTIATION_ROUNDS):
                for target in ("production", "quality", "sales"):
                    await self.send(target, "negotiate_step", {"step": it})

                changed_flags = []
                step_snapshots: List[Tuple[str, Plan, PlanMetrics]] = []
                # собрать отклики step_done от всех
                for _ in range(3):
                    msg = await self.recv(timeout=1.5)
                    if not msg:
                        continue
                    if msg.topic == "step_done":
                        p = dict_to_plan(msg.payload["plan"])
                        m = dict_to_metrics(msg.payload["metrics"])
                        changed_flags.append(bool(msg.payload.get("changed", False)))
                        step_snapshots.append((msg.sender, p, m))

                # если все ответили и никто не менял план — стабильность
                if len(changed_flags) == 3 and not any(changed_flags):
                    stabilized = True
                    break

            # 3) Запрос KPI
            for target in ("production", "quality", "sales"):
                await self.send(target, "kpi_request", {"need": "metrics"})

            reports: List[Tuple[str, Plan, PlanMetrics]] = []
            for _ in range(3):
                msg = await self.recv(timeout=1.5)
                if msg and msg.topic == "kpi_response":
                    p = dict_to_plan(msg.payload["plan"])
                    m = dict_to_metrics(msg.payload["metrics"])
                    reports.append((msg.sender, p, m))

            if reports:
                feasible = [r for r in reports if r[2].feasible]
                candidates = feasible or reports
                _, best_plan, best_metrics = max(candidates, key=lambda t: t[2].revenue)
            else:
                best_plan = current_global_plan
                best_metrics = self.env.evaluate(best_plan)

            # Лог промежуточного решения
            print(f"\n===== РАУНД {round_idx+1}: промежуточный выбор директора =====")
            print(as_table(best_plan, best_metrics))

            # 4) Принять лучший план как базовый и раздать вниз
            for target in ("production", "quality", "sales"):
                await self.send(target, "adopt_plan", {
                    "plan": best_plan.to_dict(),
                    "metrics": best_metrics.__dict__,
                })
            current_global_plan = best_plan

            # Если переговоры стабилизировались — завершаем
            if stabilized:
                break

        # Финальное объявление
        final_metrics = self.env.evaluate(current_global_plan)
        for target in ("production", "quality", "sales"):
            await self.send(target, "final_decision", {
                "plan": current_global_plan.to_dict(),
                "metrics": final_metrics.__dict__,
            })
        print("\n===== ИТОГОВЫЙ ПЛАН (директор) =====")
        print(as_table(current_global_plan, final_metrics))
