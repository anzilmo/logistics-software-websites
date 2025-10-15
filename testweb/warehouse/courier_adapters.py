# shipments/courier_adapters.py
from abc import ABC, abstractmethod
from datetime import datetime


class BaseCourierAdapter(ABC):
    @abstractmethod
    def get_status(self, tracking_number: str) -> dict:
        """
        Return a standardized dict:
        {
            "status": "in_transit" | "delivered" | "held" | ...,
            "message": "Carrier's status message",
            "location": "Optional location string",
            "timestamp": "ISO datetime string or None",
            "raw": { ... }  # raw provider payload
        }
        """
        raise NotImplementedError


class DummyCourierAdapter(BaseCourierAdapter):
    """A testing adapter — simulates status changes for demo/testing."""
    def get_status(self, tracking_number: str) -> dict:
        # naive demo logic: delivered if tracking ends with 'F', else in_transit
        status = "delivered" if tracking_number.upper().endswith("F") else "in_transit"
        return {
            "status": status,
            "message": f"Dummy carrier reports {status}",
            "location": "Distribution Center",
            "timestamp": datetime.utcnow().isoformat(),
            "raw": {"provider": "dummy", "tn": tracking_number},
        }


# Adapter registry
ADAPTERS = {
    "dummy": DummyCourierAdapter(),
    # "ups": UPSAdapter(...),
    # "fedex": FedexAdapter(...),
}


def get_adapter_for_courier(courier):
    # courier.provider_code must match ADAPTERS keys
    return ADAPTERS.get((courier.provider_code or "").lower())