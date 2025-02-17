"""iHomma SmartLight device handling."""
import socket
import logging
from typing import Optional, Tuple

from .const import UDP_PORT, TCP_PORT, PACKET_SIZES, DEBUG_NETWORK

_LOGGER = logging.getLogger(__name__)

class iHommaSML_Device:
    """Base class for iHomma device communication."""
    
    def __init__(self, device_ip: str) -> None:
        """Initialize device communication."""
        self._device_ip = device_ip
        self._udp_address = (device_ip, UDP_PORT)
        self._tcp_address = (device_ip, TCP_PORT)
        self._state = False  # Ajout de l'état interne
        self._available = False
        
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.settimeout(0.75)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._state

    @property
    def available(self) -> bool:
        """Return true if device is available."""
        return self._available

    def turn_on(self) -> bool:
        """Turn the device on."""
        result = self._send_command(0x01)
        if result:
            self._state = True
        return result

    def turn_off(self) -> bool:
        """Turn the device off."""
        result = self._send_command(0x00)
        if result:
            self._state = False
        return result

    def set_brightness(self, brightness: int) -> bool:
        """Set the brightness."""
        return self._send_command(0x02, brightness)

    def _send_command(self, command: int, data: Optional[int] = None) -> bool:
        """Send command to device."""
        try:
            # Implémentation de l'envoi de commande
            return True
        except Exception as err:
            _LOGGER.error("Failed to send command: %s", err)
            return False

    def update_state(self) -> None:
        """Update device state."""
        try:
            # Implémentation de la vérification d'état
            # Par exemple, en vérifiant la réponse du dispositif
            result = self.__getLampJSONData()
            self._available = result is not None
            if result:
                # Mise à jour de l'état en fonction de la réponse
                # self._state = ...
                _LOGGER.debug("Device %s state updated: available=%s, is_on=%s", 
                            self._device_ip, self._available, self._state)
        except Exception as err:
            self._available = False
            _LOGGER.error("Failed to update device %s state: %s", self._device_ip, err)

    def __parseMessage(self, message):
        """Converts a message to bytes if necessary"""
        _LOGGER.debug("Parsing message: %s", message)

        if type(message) == bytes:
            return message
        else:
            return message.encode()

    def __sendUDPPacket(self, address, message, wait_response=True):
        """Sends a UDP message to the specified address"""
        _LOGGER.debug("Sending UDP packet to %s:%s", address[0], address[1])

        packet = self.__parseMessage(message)
        if DEBUG_NETWORK:
            _LOGGER.debug("UDP target IP: %s", address)
            _LOGGER.debug("UDP target port: %s", UDP_PORT)
            _LOGGER.debug("message string: %s", message)
            _LOGGER.debug("message bytes: %s", packet)

        sent = self._udp_socket.sendto(packet, address)
        if wait_response:
            try:
                return self._udp_socket.recvfrom(2048)
            except Exception as e:
                _LOGGER.debug("Exception in __sendUDPPacket: %s", e)
                return None
        return sent

    def __sendTCPPacket(self, address, message, wait_response=False):
        """Sends a TCP message to the specified address"""
        _LOGGER.debug("Sending TCP packet to %s:%s", address[0], address[1])

        packet = self.__parseMessage(message)
        if DEBUG_NETWORK:
            _LOGGER.debug("TCP target IP: %s", address[0])
            _LOGGER.debug("TCP target Port: %s", address[1])
            try:
                _LOGGER.debug("Message string: %s", packet.decode())
            except Exception as e:
                _LOGGER.debug("Exception in __sendTCPPacket: %s", e)
                pass
            _LOGGER.debug("Message bytes: %s", packet)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(address)
        response = sock.send(packet)
        if wait_response:
            try:
                response = sock.recv(1024)
                return [hex(byte) for byte in response]
            except Exception as e:
                _LOGGER.debug("Exception in __sendTCPPacket: %s", e)
                return None
        _LOGGER.debug("__sendTCPPacket response: %s", response)
        return response

    def __getLampJSONData(self):
        """Get the light's JSON data"""
        _LOGGER.debug("Getting JSON data for light %s", self._attr_name)

        packet = self.__ForgeInstruction(0x2e, 0, [0xff])
        _LOGGER.debug("__getLampJSONData Packet: %s", packet)
        return self.__sendTCPPacket(self._tcp_address, packet)

    def __ForgeInstruction(self, instruction, write_switch, data, final_byte=0):
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
                _LOGGER.debug("Last byte: %s | Size: %s", last_byte, size)
                if last_byte > 255:
                    continue
                packet.append(last_byte)
                if final_byte:
                    packet.append(final_byte)
                _LOGGER.debug("Last byte: %s | Packet Size: %s", last_byte, packet_size + last_byte)
                _LOGGER.debug("Packet bytes: %s", packet)
                return bytes(packet)
        packet[2] -= 1
        packet.append(final_byte)
        _LOGGER.debug("Final Packet bytes: %s", packet)
        return bytes(packet)

    def __ConvertBrightness(self, value):
        """Convert a value from scale [0, 255] to [0, 200]."""

        """Ensure value is between 0 and 255"""
        value = max(0, min(255, value))

        converted = int(value * (200 / 255))
        _LOGGER.debug("Converting brightness from %s to %s", value, converted)
        return converted

    def __ConvertTempKelvin(self, value):
        """Convert a value from scale [2700, 6500] to [0, 200]."""

        """Ensure value is between 2700 and 6500"""
        value = max(self._attr_min_color_temp_kelvin, 
                    min(self._attr_max_color_temp_kelvin, value))

        converted = (200 - int((value - self._attr_min_color_temp_kelvin) * 200 / (self._attr_max_color_temp_kelvin - self._attr_min_color_temp_kelvin)))
        _LOGGER.debug("Converting temperature from %sK to %s", value, converted)
        return converted
    
    def __turnOnOff(self, on = False):
        """Turn the light on or off"""
        _LOGGER.info("Turning light %s %s", self._attr_name, "on" if on else "off")
        _LOGGER.debug("Execute turnOnOff: %s", "TurnOn" if on else "TurnOff")

        value = 17 if on else 18
        packet = self.__ForgeInstruction(0xa3, 1, [value])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("TurnOnOff result: %s", result)
        return result

    def __SetLuminance(self, value):
        """Set the light's brightness"""
        _LOGGER.info("Setting brightness to %s for light %s", value, self._attr_name)
        _LOGGER.debug("setBrightness : %s", value)

        converted = self.__ConvertBrightness(value)
        packet = self.__ForgeInstruction(0xa7, 1, [converted])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetLuminance result: %s", result)
        return result

    def __SetWarmth(self, value):
        """Set the light's color temperature"""
        _LOGGER.info("Setting color temperature to %sK for light %s", value, self._attr_name)
        _LOGGER.debug("setWarmth : %s°K", value)

        converted = self.__ConvertTempKelvin(value)
        packet = self.__ForgeInstruction(0xa1, 1, [converted], 94)
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetWarmth result: %s", result)
        return result

    def __SetColor(self, value):
        """Set the light's RGB color"""
        _LOGGER.info("Setting RGB color to %s for light %s", value, self._attr_name)
        _LOGGER.debug("setColor : %s", value)

        final_byte = 0
        if (value == [255, 0, 0]) or (value == [0, 255, 0]) or (value == [0, 0, 255]):
            final_byte = 94
            _LOGGER.debug("Using final byte 94 for primary color")
        packet = self.__ForgeInstruction(0xa1, 1, value, final_byte)
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetColor result: %s", result)
        return result

    def __SetPredefinedLight(self, effect):
        """Set the light's effect"""
        _LOGGER.info("Setting effect %s for light %s", effect, self._attr_name)
        _LOGGER.debug("Set Effect Light: %s ", effect)

        packet = self.__ForgeInstruction(0xa5, 1, [effect])
        result = self.__sendTCPPacket(self._tcp_address, packet)
        _LOGGER.debug("SetPredefinedLight result: %s", result)
        return result
