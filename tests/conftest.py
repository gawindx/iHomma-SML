"""Common fixtures for iHomma SmartLight tests."""
import pytest
import socket
import asyncio
from pathlib import Path
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from unittest.mock import patch, MagicMock, Mock

@pytest.fixture
async def hass(tmp_path) -> HomeAssistant:
    """Fixture pour créer une instance de HomeAssistant pour les tests."""
    hass = HomeAssistant(str(tmp_path))
    await hass.async_start()
    return hass

@pytest.fixture(autouse=True)
def mock_socket_module(monkeypatch):
    """Mock global socket module."""
    mock = Mock()
    mock.sendto.return_value = 0
    mock.recvfrom.return_value = (b"HLK_TEST", ("192.168.1.100", 988))

    class MockSocket:
        def __init__(self, *args, **kwargs):
            self.mock = mock

        def connect(self, address):
            """Simulation de la connexion TCP."""
            self.connected = True
            return None

        def sendto(self, *args):
            return self.mock.sendto(*args)
        
        def recvfrom(self, *args):
            return self.mock.recvfrom(*args)

        def send(self, data):
            """Simulation d'envoi TCP."""
            return len(data)
            
        def recv(self, bufsize):
            """Simulation de réception TCP."""
            return b'\xfe\xef\x04\xa3\x01\x11J'  # Réponse simulée

        def setsockopt(self, *args, **kwargs):
            pass
            
        def settimeout(self, *args, **kwargs):
            pass
            
        def close(self):
            self.connected = False
            
        def fileno(self):
            """Méthode requise pour les tests asyncio."""
            return 0
            
        # Ajout du support du context manager
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()
            return False

    monkeypatch.setattr("socket.socket", lambda *args, **kwargs: MockSocket())
    return mock

@pytest.fixture
def mock_light_entity():
    """Fixture to mock light entity configuration."""
    return {
        "name": "Test Light",
        "device_ip": "192.168.1.100"
    }

@pytest.fixture(autouse=True)
def allow_socket(request):
    """Fixture pour autoriser les sockets dans les tests."""
    yield