from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseMachine(ABC):
    def __init__(self, machine_id: str):
        self._machine_id = machine_id
        self._status = "offline"
        self._telemetry: Dict[str, Any] = {}

    @property
    def machine_id(self) -> str:
        return self._machine_id

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        self._status = value

    @property
    def telemetry(self) -> Dict[str, Any]:
        return self._telemetry

    @telemetry.setter
    def telemetry(self, data: Dict[str, Any]):
        self._telemetry = data

    @abstractmethod
    def generate_telemetry(self) -> Dict[str, Any]:
        """Generate machine-specific telemetry."""
        pass
