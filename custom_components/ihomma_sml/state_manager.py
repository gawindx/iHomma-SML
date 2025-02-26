"""State manager for iHomma lights."""
import logging
from typing import Dict, Any, Callable

_LOGGER = logging.getLogger(__name__)

class StateManager:
    """State manager for iHomma SmartLight integration."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._callbacks = {}
        return cls._instance

    def register_light(self, device_ip: str, callback: Callable) -> None:
        """Register a callback for a specific device."""
        if device_ip not in self._callbacks:
            self._callbacks[device_ip] = []
        self._callbacks[device_ip].append(callback)

    def unregister_light(self, device_ip: str, callback: Callable) -> None:
        """Unregister a callback for a specific device."""
        if device_ip in self._callbacks and callback in self._callbacks[device_ip]:
            self._callbacks[device_ip].remove(callback)

    def get_callbacks(self, device_ip: str) -> list:
        """Get all callbacks for a specific device."""
        return self._callbacks.get(device_ip, [])

    def update_state(self, device_ip: str, state: Dict[str, Any]) -> None:
        """Update state and notify all registered callbacks."""
        for callback in self.get_callbacks(device_ip):
            callback(state)