"""Common fixtures for iHomma SmartLight tests."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from unittest.mock import patch

@pytest.fixture
async def hass() -> HomeAssistant:
    """Fixture pour créer une instance de HomeAssistant pour les tests."""
    return HomeAssistant()

@pytest.fixture
def mock_light_entity():
    """Fixture to mock light entity configuration."""
    return {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }

@pytest.fixture
def mock_socket(monkeypatch):
    """Fixture pour mocker le socket."""
    class MockSocket:
        def __init__(self, *args, **kwargs):
            pass
            
        def setsockopt(self, *args, **kwargs):
            pass
            
        def settimeout(self, *args, **kwargs):
            pass
            
        def sendto(self, *args, **kwargs):
            return 0
            
        def recvfrom(self, *args, **kwargs):
            return b"HLK_TEST", ("192.168.1.100", 988)
            
        def close(self):
            pass
    
    monkeypatch.setattr("socket.socket", MockSocket)