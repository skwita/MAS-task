from typing import Any, Dict

from model.data.Plan import Plan
from model.data.PlanMetrics import PlanMetrics


def dict_to_plan(d: Dict[str, Any]) -> Plan:
    return Plan(
        batches=int(d["batches"]),
        replace_equip=int(d["replace_equip"]),
        better_materials=bool(d["better_materials"]),
        better_staff=bool(d["better_staff"]),
    )

def dict_to_metrics(d: Dict[str, Any]) -> PlanMetrics:
    return PlanMetrics(
        feasible=bool(d["feasible"]),
        reason=str(d["reason"]),
        produced_units=int(d["produced_units"]),
        defective_units=int(d["defective_units"]),
        saleable_units=int(d["saleable_units"]),
        revenue=int(d["revenue"]),
        total_cost=int(d["total_cost"]),
        cash_left=int(d["cash_left"]),
    )

def as_table(plan: Plan, m: PlanMetrics) -> str:
    lines = [
        f"План: партии={plan.batches}, замена_оборудования={plan.replace_equip}, материалы+7%={plan.better_materials}, персонал+20%={plan.better_staff}",
        f"Произведено: {m.produced_units} ед.",
        f"Брак: {m.defective_units} ед.",
        f"К реализации: {m.saleable_units} ед.",
        f"Выручка: {m.revenue:,.0f} руб.",
        f"Затраты: {m.total_cost:,.0f} руб.",
        f"Остаток денежных средств: {m.cash_left:,.0f} руб.",
        f"Выполнимость: {'да' if m.feasible else 'нет'} ({m.reason})",
    ]
    return "\n".join(lines)