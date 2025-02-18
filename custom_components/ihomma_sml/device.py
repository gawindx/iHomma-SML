"""Device handling for iHomma SmartLight integration."""
import socket
import logging
from typing import Dict, Any, Optional

from homeassistant.const import STATE_ON, STATE_OFF

from .const import (
    UDP_PORT,
    TCP_PORT,
    PACKET_SIZES,
    DEBUG_NETWORK,
)
from .state_manager import StateManager

_LOGGER = logging.getLogger(__name__)

class iHommaSML_Device:
    """Gestion de la communication avec une ampoule iHomma."""

    def __init__(self, device_ip: str) -> None:
        """Initialize device communication."""
        self._device_ip = device_ip
        self._udp_address = (device_ip, UDP_PORT)
        self._tcp_address = (device_ip, TCP_PORT)
        self._available = False
        self._state = False
        self._brightness = 255
        self._color_temp = 4000
        self._effect = None
        self._attr_min_color_temp_kelvin = 2700
        self._attr_max_color_temp_kelvin = 6500
        self._rgb_color = (255, 255, 255)
        self._last_command_success = False  # Nouvel attribut pour suivre le succès des commandes
        self._state_manager = StateManager()

        # Création du socket UDP réutilisable
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.settimeout(0.75)

    @property
    def device_ip(self) -> str:
        """Return device IP."""
        return self._device_ip

    @property
    def available(self) -> bool:
        """Return if device is available."""
        _LOGGER.debug("Checking availability for light %s", self._device_ip)
        self._available = self.__sendUDPPacket(self._udp_address, "HLK") is not None
        return self._available

    @property
    def is_on(self) -> bool:
        """Return if device is on."""
        return self._state

    def __parseMessage(self, message) -> dict:
        """Parse JSON message from device."""
        _LOGGER.debug("Parsing message: %s", message)

        try:
            # Décodage JSON si nécessaire
            if isinstance(message, bytes):
                return message
            else:
                return message.encode()
        except Exception as err:
            _LOGGER.error("Error parsing message from %s: %s", self._device_ip, err)
            return {}

    def __sendUDPPacket(self, address: tuple, message: bytes,wait_response: bool = True) -> Optional[dict]:
        """Send UDP packet."""
        _LOGGER.debug("Sending UDP packet to %s:%s", address[0], address[1])

        packet = self.__parseMessage(message)
        if DEBUG_NETWORK:
            _LOGGER.debug("Sending UDP to %s:%d: %s", address[0], address[1], message.hex())
        try:
            result = self._udp_socket.sendto(packet, address)
            if wait_response:
                result = self._udp_socket.recvfrom(2048)
        except Exception as err:
            _LOGGER.error("UDP communication error with %s: %s", self._device_ip, err)
            result = None
        finally:
            self._last_command_success = result is not None
            return result

    def __sendTCPPacket(self, address: tuple, message: bytes, wait_response:bool = False) -> Optional[dict]:
        """Send TCP packet and return response."""
        _LOGGER.debug("Sending TCP packet to %s:%s", address[0], address[1])

        if DEBUG_NETWORK:
            _LOGGER.debug("Sending TCP to %s:%d: %s", address[0], address[1], message.hex())
        packet = self.__parseMessage(message)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
                tcp_sock.settimeout(0.75)
                tcp_sock.connect(address)
                tcp_sock.send(message)
                response = True
                if wait_response:
                    response = tcp_sock.recv(PACKET_SIZES['TCP'])
                    if DEBUG_NETWORK:
                        _LOGGER.debug("Received TCP from %s:%d: %s", address[0], address[1], response.hex())
                    return [hex(byte) for byte in response]
                _LOGGER.debug("__sendTCPPacket response: %s", response)
                return response
        except Exception as err:
            _LOGGER.error("TCP communication error with %s: %s", self._device_ip, err)
            self._available = False
            return False

    def __ForgeInstruction(self, instruction: int, write_switch: int, data: list, final_byte:int = 0) -> bytes:
        """Forge an instruction packet for the light"""
        _LOGGER.debug("Forging instruction: 0x%x with data %s", instruction, data)

        header = [0xfe, 0xef]
        message_length = len(data) + 1 + 1 + 1 + (1 if final_byte else 0)# données + instruction + write_switch + last_byte

        packet = header + [message_length, instruction, write_switch] + data
        packet_size = final_byte
        last_byte = 0
        for byte in packet:
            packet_size += byte
        for size in PACKET_SIZES:
            if size >= packet_size:
                last_byte = size - packet_size + (1 if final_byte else 0)
                if DEBUG_NETWORK:
                    _LOGGER.debug("Last byte: %s | Size: %s", last_byte, size)
                if last_byte > 255:
                    continue
                packet.append(last_byte)
                if final_byte:
                    packet.append(final_byte)
                if DEBUG_NETWORK:
                    _LOGGER.debug("Last byte: %s | Packet Size: %s", last_byte, packet_size + last_byte)
                    _LOGGER.debug("Packet bytes: %s", packet)
                return bytes(packet)
        packet[2] -= 1
        packet.append(final_byte)
        _LOGGER.debug("Forged instruction: %s", packet.hex())
        return bytes(packet)

    def __turnOnOff(self, on:bool = False):
        """Turn the light on or off"""
        _LOGGER.info("Turning light %s %s", self._device_ip, "on" if on else "off")
        _LOGGER.debug("Execute turnOnOff: %s", "TurnOn" if on else "TurnOff")

        value = 17 if on else 18
        packet = self.__ForgeInstruction(0xa3, 1, [value])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("TurnOnOff result: %s", result)
        return result

    def get_state(self) -> Dict[str, Any]:
        """Get cached device state."""
        _LOGGER.debug("Checking availability for light %s", self._device_ip)
        
        watchdog = self.__sendUDPPacket(self._udp_address, "HLK")
        return {
            "available": watchdog is not None,  # Basé sur la dernière commande
            "state": STATE_ON if self._state else STATE_OFF,
            "brightness": self._brightness,
            "color_temp": self._color_temp,
            "rgb_color": self._rgb_color,
            "effect": self._effect
        }

    def _notify_state_change(self) -> None:
        """Notify state changes."""
        state = {
            "state": STATE_ON if self._state else STATE_OFF,
            "brightness": self._brightness,
            "color_temp": self._color_temp,
            "rgb_color": self._rgb_color,
            "effect": self._effect
        }
        self._state_manager.update_state(self._device_ip, state)

    def turn_on(self) -> bool:
        """Turn the device on."""
        _LOGGER.debug("Turning on Device %s", self._device_ip)
        if self.__turnOnOff(True):
            self._state = True
            self._notify_state_change()
            _LOGGER.debug("Device %s Turned On", self._device_ip)
            return True
        else:
            return False

    def turn_off(self) -> bool:
        """Turn the device off."""
        _LOGGER.debug("Turning off Device %s", self._device_ip)
        if self.__turnOnOff():
            self._state = False
            self._notify_state_change()
            _LOGGER.debug("Device %s Turned On", self._device_ip)
            return True
        else:
            return False

    def __ConvertBrightness(self, value):
        """Convert a value from scale [0, 255] to [0, 200]."""

        """Ensure value is between 0 and 255"""
        value = max(0, min(255, value))

        converted = int(value * (200 / 255))
        _LOGGER.debug("Converting brightness from %s to %s", value, converted)
        return converted

    def set_brightness(self, brightness: int) -> bool:
        """Set device brightness."""
        _LOGGER.info("Setting brightness to %s for light %s", brightness, self._device_ip)
        _LOGGER.debug("setBrightness : %s", brightness)

        converted_brightness = self.__ConvertBrightness(brightness)
        packet = self.__ForgeInstruction(0xa7, 1, [converted_brightness])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        if result is not None:
            self._brightness = brightness
            self._notify_state_change()
            return True
        return False

    def __ConvertTempKelvin(self, value):
        """Convert a value from scale [2700, 6500] to [0, 200]."""

        """Ensure value is between 2700 and 6500"""
        value = max(self._attr_min_color_temp_kelvin, 
                    min(self._attr_max_color_temp_kelvin, value))

        converted = (200 - int((value - self._attr_min_color_temp_kelvin) * 200 / (self._attr_max_color_temp_kelvin - self._attr_min_color_temp_kelvin)))
        _LOGGER.debug("Converting temperature from %sK to %s", value, converted)
        return converted

    def set_temperature(self, temperature: int) -> bool:
        """Set color temperature."""
        # Conversion en valeur compatible avec l'ampoule si nécessaire
        converted_temp = self.__ConvertTempKelvin(temperature)
        packet = self.__ForgeInstruction(0xa1, 1, [converted_temp], 94)
        result = self.__sendTCPPacket(self._tcp_address, packet)
        if result is not None:
            self._color_temp = temperature
            self._notify_state_change()
            return True
        return False

    def set_color(self, rgb: tuple[int, int, int]) -> bool:
        """Set the light's RGB color"""
        _LOGGER.info("Setting RGB color to %s for light %s", rgb, self._device_ip)
        _LOGGER.debug("setColor : %s", rgb)

        final_byte = 0
        if (rgb == [255, 0, 0]) or (rgb == [0, 255, 0]) or (rgb == [0, 0, 255]):
            final_byte = 94
            _LOGGER.debug("Using final byte 94 for primary color")
        packet = self.__ForgeInstruction(0xa1, 1, list(rgb), final_byte)
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetColor result: %s", result)
        if result is not None:
            self._rgb_color = rgb
            self._notify_state_change()
            return True
        return False

    def set_effect(self, effect_instruction: int, effect_name: str) -> bool:
        """Set the light's effect"""
        _LOGGER.info("Setting effect %s for light %s", effect_instruction, self._device_ip)
        _LOGGER.debug("Set Effect Light: %s ", effect_instruction)

        packet = self.__ForgeInstruction(0xa5, 1, [effect_instruction])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetEffect result: %s", result)
        if result is not None:
            self._effect = effect_name
            self._notify_state_change()
            return True
        return False
