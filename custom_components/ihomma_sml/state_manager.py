"""State manager for iHomma lights."""
import logging
from typing import Dict, Any, Callable

_LOGGER = logging.getLogger(__name__)

class StateManager:
    """Manage shared state between individual lights and groups."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._states = {}
            cls._instance._subscribers = {}
        return cls._instance

    def register_light(self, device_ip: str, callback: Callable) -> None:
        """Register a light for state updates."""
        if device_ip not in self._subscribers:
            self._subscribers[device_ip] = set()
        self._subscribers[device_ip].add(callback)

    def unregister_light(self, device_ip: str, callback: Callable) -> None:
        """Unregister a light."""
        if device_ip in self._subscribers:
            self._subscribers[device_ip].discard(callback)

    def update_state(self, device_ip: str, state: Dict[str, Any]) -> None:
        """Update state and notify subscribers."""
        self._states[device_ip] = state
        if device_ip in self._subscribers:
            for callback in self._subscribers[device_ip]:
                callback(state)