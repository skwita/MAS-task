from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Plan:
    batches: int
    replace_equip: int
    better_materials: bool
    better_staff: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batches": self.batches,
            "replace_equip": self.replace_equip,
            "better_materials": self.better_materials,
            "better_staff": self.better_staff,
        }