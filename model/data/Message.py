from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Message:
    sender: str
    receiver: str
    topic: str
    payload: Dict[str, Any]