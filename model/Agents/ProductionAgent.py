from typing import List, Tuple
from model.Agents.Agent import Agent
from model.data.Plan import Plan
from util.Util import dict_to_plan


class ProductionAgent(Agent):
    """
    Цель: повышать выпуск (produced_units). Работает итеративно:
    - принимает базовый план от директора (decision_round/adopt_plan)
    - на шаге negotiate_step генерирует локальное улучшение и рассылает предложение
    - принимает чужие предложения и, если они лучше по локальной метрике, принимает
    - отчитывается директору step_done(changed, plan, metrics)
    - по kpi_request отдаёт свой текущий план
    - по final_decision завершает работу
    """
    def score(self, plan: Plan) -> float:
        m = self.env.evaluate(plan)
        return float(m.produced_units) if m.feasible else -1e9

    def neighborhood(self, base: Plan) -> List[Plan]:
        res: List[Plan] = []
        for b in [max(1, base.batches-1), base.batches, min(4, base.batches+1)]:
            for repl in [base.replace_equip, min(6, base.replace_equip+2)]:
                res.append(Plan(b, repl, base.better_materials, base.better_staff))
        return res

    async def run(self):
        current: Plan = Plan(2, 0, False, False)
        while True:
            msg = await self.recv(timeout=10.0)
            if not msg:
                continue

            if msg.topic in ("decision_round", "adopt_plan"):
                current = dict_to_plan(msg.payload["plan"])

            elif msg.topic == "negotiate_step":
                changed = False
                # 1) собственное улучшение
                candidates = self.neighborhood(current)
                best_local = max(candidates+[current], key=self.score)
                if self.score(best_local) > self.score(current):
                    current = best_local
                    changed = True
                # 2) разослать своё предложение
                for target in ("quality", "sales"):
                    await self.send(target, "proposal", {"plan": current.to_dict()})
                # 3) принять предложения коллег (окно небольшое)
                while True:
                    inc = await self.recv(timeout=0.2)
                    if not inc:
                        break
                    if inc.topic == "proposal":
                        p = dict_to_plan(inc.payload["plan"])
                        if self.score(p) > self.score(current):
                            current = p
                            changed = True
                # 4) отчёт директору
                await self.send("director", "step_done", {
                    "changed": changed,
                    "plan": current.to_dict(),
                    "metrics": self.env.evaluate(current).__dict__,
                })

            elif msg.topic == "kpi_request":
                await self.send("director", "kpi_response", {
                    "plan": current.to_dict(),
                    "metrics": self.env.evaluate(current).__dict__,
                })

            elif msg.topic == "final_decision":
                break
