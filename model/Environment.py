from model.data.Plan import Plan
from model.data.PlanMetrics import PlanMetrics


class Environment:

    def __init__(self):
        pass

    def evaluate(self, plan: Plan) -> PlanMetrics:
        return PlanMetrics(True, "", 1, 1, 1, 1, 1, 1)