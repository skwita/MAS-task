import math
from typing import Tuple
from model.data.Plan import Plan
from model.data.PlanMetrics import PlanMetrics
from model.config import (EQUIPMENT_NUM, CAP_PER_EQUIP_AT_100, NEW_EQUIP_FACTOR,
                          BATCH_DEFECT, PRICE_MATERIAL_BATCH,UNIT_PRICE,
                          BATCH_SIZE, BUDGET, PRICE_HUMAN_BATHC)


class Environment:
    total_equip: int
    def init(self):
        # базовое количество старых и потенциально новых единиц оборудования
        self.total_equip = EQUIPMENT_NUM

    def equipment_profile(self, replace_equip: int) -> Tuple[int, int]:
        replace_equip = max(0, min(replace_equip, self.total_equip))
        return self.total_equip - replace_equip, replace_equip

    def capacity_units(self, replace_equip: int, utilization: float = 0.75) -> int:
        """Месячная мощность по выпуску (единиц), исходя из текущей загрузки.
        Старыe — CAP_PER_EQUIP_AT_100, новые — умножаем на NEW_EQUIP_FACTOR.
        """
        old_e, new_e = self.equipment_profile(replace_equip)
        cap_old = old_e * CAP_PER_EQUIP_AT_100 * utilization
        cap_new = new_e * CAP_PER_EQUIP_AT_100 * NEW_EQUIP_FACTOR * utilization
        return math.floor(cap_old + cap_new)

    def defect_rate(self, better_materials: bool, better_staff: bool) -> float:
        dr = BATCH_DEFECT
        if better_materials:
            dr -= 0.01
        if better_staff:
            dr -= 0.02
        return max(0.0, dr)

    def costs(self, plan: Plan) -> int:
        mat_cost = PRICE_MATERIAL_BATCH * plan.batches
        pay_cost = PRICE_HUMAN_BATHC * plan.batches
        # корректировки качества
        if plan.better_materials:
            mat_cost = int(round(mat_cost * 1.07))
        if plan.better_staff:
            pay_cost = int(round(pay_cost * 1.20))
        equip_cost = plan.replace_equip * 120_000
        return mat_cost + pay_cost + equip_cost

    def demand_cap(self, plan: Plan, defective_units: int) -> int:
        # Сбыт гарантирует сохранение спроса при увеличении числа партий вдвое => до 4 партий
        base_demand = plan.batches * BATCH_SIZE
        if plan.batches > 4:
            base_demand = 4 * BATCH_SIZE
        # Если брак > 150 ед., спрос падает в 2 раза
        if defective_units > 150:
            base_demand //= 2
        return base_demand

    def evaluate(self, plan: Plan) -> PlanMetrics:
        # Выпуск по партиям (технологический запрос)
        requested_units = plan.batches * BATCH_SIZE
        # Производственная мощность (при текущей загрузке)
        cap_units = self.capacity_units(plan.replace_equip, utilization=0.75)
        produced_units = min(requested_units, cap_units)

        # Дефект
        dr = self.defect_rate(plan.better_materials, plan.better_staff)
        defective_units = math.floor(produced_units * dr)

        # Спрос/сбыт
        demand = self.demand_cap(plan, defective_units)
        saleable_units = min(produced_units - defective_units, demand)

        # Финансы
        total_cost = self.costs(plan)
        feasible = total_cost <= BUDGET
        revenue = saleable_units * UNIT_PRICE
        cash_left = BUDGET - total_cost

        reason = "OK" if feasible else "Превышен денежный фонд"

        return PlanMetrics(
            feasible=feasible,
            reason=reason,
            produced_units=produced_units,
            defective_units=defective_units,
            saleable_units=saleable_units,
            revenue=revenue,
            total_cost=total_cost,
            cash_left=cash_left,
        )