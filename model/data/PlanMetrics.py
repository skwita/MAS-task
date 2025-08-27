from dataclasses import dataclass


@dataclass
class PlanMetrics:
    feasible: bool
    reason: str
    produced_units: int
    defective_units: int
    saleable_units: int
    revenue: int
    total_cost: int
    cash_left: int